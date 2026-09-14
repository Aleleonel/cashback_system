from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError
from django.db import transaction

from auditoria.models import RegistroAuditoria
from auditoria.services import registrar_auditoria

from .models import BaixaFinanceira, ParcelaFinanceira, TituloFinanceiro


def _decimal_positivo(valor, campo):
    try:
        convertido = Decimal(str(valor))
    except (InvalidOperation, TypeError, ValueError):
        raise ValidationError({campo: "Informe um valor monetario valido."})
    if convertido <= 0:
        raise ValidationError({campo: "O valor deve ser maior que zero."})
    return convertido


@transaction.atomic
def criar_titulo_financeiro(
    *,
    matriz,
    loja,
    natureza,
    origem_tipo,
    origem_id,
    chave_idempotencia,
    descricao,
    data_emissao,
    parcelas,
    usuario=None,
    request=None,
):
    if loja is not None and loja.matriz_id != matriz.id:
        raise ValidationError(
            {"loja": "A loja informada deve pertencer a matriz do titulo."}
        )
    existente = (
        TituloFinanceiro.objects.select_for_update()
        .filter(matriz=matriz, chave_idempotencia=chave_idempotencia)
        .first()
    )
    parcelas = list(parcelas or [])

    if existente is not None:
        total_requisitado = Decimal("0.00")
        for item in parcelas:
            total_requisitado += _decimal_positivo(item.get("valor"), "valor")
        conflito = (
            existente.natureza != natureza
            or existente.origem_tipo != origem_tipo
            or existente.origem_id != origem_id
            or existente.loja_id != (loja.pk if loja is not None else None)
            or existente.descricao != descricao
            or existente.data_emissao != data_emissao
            or existente.valor_original != total_requisitado
        )
        if conflito:
            raise ValidationError(
                {"chave_idempotencia": "A chave ja existe com dados financeiros diferentes."}
            )
        estrutura_solicitada = sorted(
            (
                int(item["numero"]),
                item["vencimento"],
                _decimal_positivo(item["valor"], "valor"),
            )
            for item in parcelas
        )
        estrutura_existente = list(
            existente.parcelas.order_by("numero").values_list(
                "numero", "vencimento", "valor_original"
            )
        )
        if estrutura_existente != estrutura_solicitada:
            raise ValidationError(
                {"chave_idempotencia": "A chave ja existe com estrutura de parcelas diferente."}
            )
        return existente

    if not parcelas:
        raise ValidationError({"parcelas": "Informe ao menos uma parcela."})

    numeros = []
    parcelas_normalizadas = []
    total = Decimal("0.00")
    for item in parcelas:
        numero = item.get("numero")
        vencimento = item.get("vencimento")
        valor = _decimal_positivo(item.get("valor"), "valor")
        if not isinstance(numero, int) or isinstance(numero, bool) or numero <= 0:
            raise ValidationError({"numero": "O numero da parcela deve ser inteiro positivo."})
        if numero in numeros:
            raise ValidationError({"numero": "Os numeros das parcelas nao podem se repetir."})
        if vencimento is None:
            raise ValidationError({"vencimento": "O vencimento e obrigatorio."})
        numeros.append(numero)
        parcelas_normalizadas.append((numero, vencimento, valor))
        total += valor

    titulo = TituloFinanceiro(
        matriz=matriz,
        loja=loja,
        natureza=natureza,
        origem_tipo=origem_tipo,
        origem_id=origem_id,
        chave_idempotencia=chave_idempotencia,
        descricao=descricao,
        valor_original=total,
        status=TituloFinanceiro.Status.ABERTO,
        data_emissao=data_emissao,
    )
    titulo.full_clean()
    titulo.save()

    for numero, vencimento, valor in parcelas_normalizadas:
        parcela = ParcelaFinanceira(
            titulo=titulo,
            numero=numero,
            vencimento=vencimento,
            valor_original=valor,
            status=ParcelaFinanceira.Status.ABERTO,
        )
        parcela.full_clean()
        parcela.save()

    registrar_auditoria(
        usuario=usuario,
        matriz=titulo.matriz,
        loja=titulo.loja,
        acao=RegistroAuditoria.ACAO_CRIAR,
        recurso="financeiro.titulo",
        recurso_id=titulo.uuid,
        descricao=f"Titulo financeiro criado: uuid={titulo.uuid}; natureza={titulo.natureza}; valor={titulo.valor_original}.",
        request=request,
    )

    return titulo

def _sincronizar_status_titulo(titulo):
    parcelas = list(titulo.parcelas.all())
    if parcelas and all(p.status == ParcelaFinanceira.Status.LIQUIDADO for p in parcelas):
        novo_status = TituloFinanceiro.Status.LIQUIDADO
    elif any(p.status in (ParcelaFinanceira.Status.PARCIAL, ParcelaFinanceira.Status.LIQUIDADO) for p in parcelas):
        novo_status = TituloFinanceiro.Status.PARCIAL
    else:
        novo_status = TituloFinanceiro.Status.ABERTO
    if titulo.status != novo_status:
        titulo.status = novo_status
        titulo.save(update_fields=["status", "atualizado_em"])


@transaction.atomic
def registrar_baixa_financeira(
    *,
    parcela,
    valor,
    data,
    chave_idempotencia,
    observacao="",
    usuario=None,
    request=None,
):
    parcela = (
        ParcelaFinanceira.objects.select_for_update()
        .select_related("titulo")
        .get(pk=parcela.pk)
    )
    titulo = TituloFinanceiro.objects.select_for_update().get(pk=parcela.titulo_id)
    if titulo.status == TituloFinanceiro.Status.CANCELADO or parcela.status == ParcelaFinanceira.Status.CANCELADO:
        raise ValidationError({"parcela": "Nao e permitido registrar baixa em titulo ou parcela cancelada."})
    valor = _decimal_positivo(valor, "valor")

    existente = (
        BaixaFinanceira.objects.select_for_update()
        .filter(parcela=parcela, chave_idempotencia=chave_idempotencia)
        .first()
    )
    if existente is not None:
        if (
            existente.tipo != BaixaFinanceira.Tipo.BAIXA
            or existente.valor != valor
            or existente.data != data
            or existente.observacao != observacao
        ):
            raise ValidationError(
                {"chave_idempotencia": "A chave ja existe com dados de baixa diferentes."}
            )
        return existente

    eventos = list(parcela.baixas.all())
    total_baixas = sum(
        (evento.valor for evento in eventos if evento.tipo == BaixaFinanceira.Tipo.BAIXA),
        Decimal("0.00"),
    )
    total_estornos = sum(
        (evento.valor for evento in eventos if evento.tipo == BaixaFinanceira.Tipo.ESTORNO),
        Decimal("0.00"),
    )
    saldo = parcela.valor_original - total_baixas + total_estornos
    if valor > saldo:
        raise ValidationError({"valor": "A baixa nao pode exceder o saldo da parcela."})

    baixa = BaixaFinanceira(
        parcela=parcela,
        valor=valor,
        data=data,
        tipo=BaixaFinanceira.Tipo.BAIXA,
        chave_idempotencia=chave_idempotencia,
        observacao=observacao,
    )
    baixa.full_clean()
    baixa.save()

    saldo_restante = saldo - valor
    if saldo_restante == Decimal("0.00"):
        parcela.status = ParcelaFinanceira.Status.LIQUIDADO
    else:
        parcela.status = ParcelaFinanceira.Status.PARCIAL
    parcela.save(update_fields=["status"])
    _sincronizar_status_titulo(titulo)
    registrar_auditoria(
        usuario=usuario,
        matriz=titulo.matriz,
        loja=titulo.loja,
        acao=RegistroAuditoria.ACAO_CRIAR,
        recurso="financeiro.baixa",
        recurso_id=baixa.pk,
        descricao=f"Baixa financeira registrada: id={baixa.pk}; valor={baixa.valor}.",
        request=request,
    )
    return baixa

@transaction.atomic
def estornar_baixa_financeira(
    *,
    baixa,
    valor,
    data,
    chave_idempotencia,
    observacao="",
    usuario=None,
    request=None,
):
    baixa_original = (
        BaixaFinanceira.objects.select_for_update()
        .select_related("parcela__titulo")
        .get(pk=baixa.pk)
    )
    if baixa_original.tipo != BaixaFinanceira.Tipo.BAIXA:
        raise ValidationError({"baixa": "Somente um evento de baixa pode ser estornado."})

    parcela = ParcelaFinanceira.objects.select_for_update().get(pk=baixa_original.parcela_id)
    titulo = TituloFinanceiro.objects.select_for_update().get(pk=parcela.titulo_id)
    valor = _decimal_positivo(valor, "valor")

    existente = (
        BaixaFinanceira.objects.select_for_update()
        .filter(parcela=parcela, chave_idempotencia=chave_idempotencia)
        .first()
    )
    if existente is not None:
        if (
            existente.tipo != BaixaFinanceira.Tipo.ESTORNO
            or existente.valor != valor
            or existente.data != data
            or existente.observacao != observacao
        ):
            raise ValidationError(
                {"chave_idempotencia": "A chave ja existe com dados de estorno diferentes."}
            )
        return existente

    eventos = list(parcela.baixas.all())
    total_baixas = sum(
        (evento.valor for evento in eventos if evento.tipo == BaixaFinanceira.Tipo.BAIXA),
        Decimal("0.00"),
    )
    total_estornos = sum(
        (evento.valor for evento in eventos if evento.tipo == BaixaFinanceira.Tipo.ESTORNO),
        Decimal("0.00"),
    )
    total_liquido_baixado = total_baixas - total_estornos
    if valor > total_liquido_baixado:
        raise ValidationError({"valor": "O estorno nao pode exceder o total liquido baixado."})

    estorno = BaixaFinanceira(
        parcela=parcela,
        valor=valor,
        data=data,
        tipo=BaixaFinanceira.Tipo.ESTORNO,
        chave_idempotencia=chave_idempotencia,
        observacao=observacao,
    )
    estorno.full_clean()
    estorno.save()

    total_liquido_apos = total_liquido_baixado - valor
    if total_liquido_apos == Decimal("0.00"):
        parcela.status = ParcelaFinanceira.Status.ABERTO
    elif total_liquido_apos < parcela.valor_original:
        parcela.status = ParcelaFinanceira.Status.PARCIAL
    else:
        parcela.status = ParcelaFinanceira.Status.LIQUIDADO
    parcela.save(update_fields=["status"])
    _sincronizar_status_titulo(titulo)
    registrar_auditoria(
        usuario=usuario,
        matriz=titulo.matriz,
        loja=titulo.loja,
        acao=RegistroAuditoria.ACAO_CRIAR,
        recurso="financeiro.estorno",
        recurso_id=estorno.pk,
        descricao=f"Estorno financeiro registrado: id={estorno.pk}; baixa_origem={baixa.pk}; valor={estorno.valor}.",
        request=request,
    )
    return estorno

@transaction.atomic
def cancelar_titulo_financeiro(*, titulo, usuario=None, request=None):
    titulo = TituloFinanceiro.objects.select_for_update().get(pk=titulo.pk)

    if titulo.status == TituloFinanceiro.Status.CANCELADO:
        return titulo

    parcelas = list(
        ParcelaFinanceira.objects.select_for_update()
        .filter(titulo=titulo)
        .prefetch_related("baixas")
        .order_by("numero")
    )

    total_liquido_baixado = Decimal("0.00")
    for parcela in parcelas:
        total_baixas = sum(
            (evento.valor for evento in parcela.baixas.all() if evento.tipo == BaixaFinanceira.Tipo.BAIXA),
            Decimal("0.00"),
        )
        total_estornos = sum(
            (evento.valor for evento in parcela.baixas.all() if evento.tipo == BaixaFinanceira.Tipo.ESTORNO),
            Decimal("0.00"),
        )
        total_liquido_baixado += total_baixas - total_estornos

    if total_liquido_baixado != Decimal("0.00"):
        raise ValidationError(
            {"titulo": "O titulo somente pode ser cancelado quando o total liquido baixado for zero."}
        )

    for parcela in parcelas:
        if parcela.status != ParcelaFinanceira.Status.CANCELADO:
            parcela.status = ParcelaFinanceira.Status.CANCELADO
            parcela.save(update_fields=["status"])

    titulo.status = TituloFinanceiro.Status.CANCELADO
    titulo.save(update_fields=["status", "atualizado_em"])
    registrar_auditoria(
        usuario=usuario,
        matriz=titulo.matriz,
        loja=titulo.loja,
        acao=RegistroAuditoria.ACAO_EDITAR,
        recurso="financeiro.titulo",
        recurso_id=titulo.uuid,
        descricao=f"Titulo financeiro cancelado: uuid={titulo.uuid}.",
        request=request,
    )
    return titulo
