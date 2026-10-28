from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from auditoria.models import RegistroAuditoria
from auditoria.services import registrar_auditoria

from .models import BaixaFinanceira, CentroCusto, FechamentoGerencial, ParcelaFinanceira, PlanoConta, TituloFinanceiro
from django.core.exceptions import PermissionDenied
from accounts.permissions import PERMISSAO_FINANCEIRO_EDITAR_LANCAMENTO, PERMISSAO_FINANCEIRO_CANCELAR_LANCAMENTO, PERMISSAO_FINANCEIRO_REABRIR_COMPETENCIA
from accounts.services import usuario_tem_permissao


def _exigir_escopo_titulo_financeiro(*, usuario, titulo):
    if usuario is None or getattr(usuario, "pk", None) is None:
        raise PermissionDenied("Usuario invalido para operacao financeira.")
    if getattr(usuario, "is_superuser", False):
        return
    if usuario.matriz_id != titulo.matriz_id:
        raise PermissionDenied("Titulo financeiro fora da matriz autorizada.")
    perfil = getattr(usuario, "perfil", None)
    if perfil == "master":
        return
    if perfil in ("admin_loja", "operador"):
        if titulo.loja_id is None or not usuario.lojas.filter(
            pk=titulo.loja_id, matriz_id=titulo.matriz_id
        ).exists():
            raise PermissionDenied("Titulo financeiro fora das lojas autorizadas para o usuario.")


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

@transaction.atomic
def criar_lancamento_manual(
    *,
    matriz,
    loja,
    natureza,
    chave_idempotencia,
    descricao,
    data_emissao,
    parcelas,
    plano_conta,
    centro_custo=None,
    entidade_nome="",
    documento_referencia="",
    data_competencia=None,
    valor_bruto=None,
    valor_desconto="0.00",
    valor_juros="0.00",
    observacao="",
    usuario=None,
    request=None,
):
    if plano_conta is None:
        raise ValidationError({"plano_conta": "O plano de contas e obrigatorio."})
    plano_conta = PlanoConta.objects.get(pk=plano_conta.pk)
    if plano_conta.matriz_id != matriz.pk:
        raise ValidationError({"plano_conta": "O plano de contas deve pertencer a matriz do lancamento."})
    if not plano_conta.ativo:
        raise ValidationError({"plano_conta": "O plano de contas deve estar ativo."})
    if plano_conta.tipo != PlanoConta.Tipo.ANALITICA or not plano_conta.aceita_lancamento:
        raise ValidationError({"plano_conta": "O plano de contas deve ser analitico e aceitar lancamentos."})
    if loja is not None and loja.matriz_id != matriz.pk:
        raise ValidationError({"loja": "A loja deve pertencer a matriz do lancamento."})
    if centro_custo is not None:
        centro_custo = CentroCusto.objects.get(pk=centro_custo.pk)
        if centro_custo.matriz_id != matriz.pk:
            raise ValidationError({"centro_custo": "O centro de custo deve pertencer a matriz do lancamento."})
        if not centro_custo.ativo:
            raise ValidationError({"centro_custo": "O centro de custo deve estar ativo."})

    if data_competencia is None:
        raise ValidationError({"data_competencia": "A data de competencia e obrigatoria no lancamento manual."})
    if valor_bruto is None:
        raise ValidationError({"valor_bruto": "O valor bruto e obrigatorio no lancamento manual."})
    valor_bruto = _decimal_positivo(valor_bruto, "valor_bruto")
    try:
        valor_desconto = Decimal(str(valor_desconto))
        valor_juros = Decimal(str(valor_juros))
    except Exception as exc:
        raise ValidationError({"valores": "Desconto e juros devem ser valores decimais validos."}) from exc
    if valor_desconto < 0 or valor_juros < 0:
        raise ValidationError({"valores": "Desconto e juros nao podem ser negativos."})
    valor_final = valor_bruto - valor_desconto + valor_juros
    if valor_final <= 0:
        raise ValidationError({"valor_final": "O valor final deve ser maior que zero."})

    soma_parcelas = Decimal("0.00")
    for item in parcelas:
        soma_parcelas += Decimal(str(item["valor"]))
    if soma_parcelas != valor_final:
        raise ValidationError({"parcelas": "A soma das parcelas deve ser igual ao valor final."})

    centro_custo_id = centro_custo.pk if centro_custo is not None else None
    existente = (
        TituloFinanceiro.objects.select_for_update()
        .filter(matriz=matriz, chave_idempotencia=chave_idempotencia)
        .first()
    )
    if existente is not None:
        conflito = (
            existente.loja_id != (loja.pk if loja is not None else None)
            or existente.natureza != natureza
            or existente.origem_tipo != TituloFinanceiro.OrigemTipo.MANUAL
            or existente.origem_id != chave_idempotencia
            or existente.descricao != descricao
            or existente.data_emissao != data_emissao
            or existente.plano_conta_id != plano_conta.pk
            or existente.centro_custo_id != centro_custo_id
            or existente.entidade_nome != entidade_nome
            or existente.documento_referencia != documento_referencia
            or existente.data_competencia != data_competencia
            or existente.valor_bruto != valor_bruto
            or existente.valor_desconto != valor_desconto
            or existente.valor_juros != valor_juros
            or existente.observacao != observacao
            or existente.valor_original != valor_final
        )
        estrutura = [
            (p.numero, p.vencimento, p.valor_original)
            for p in existente.parcelas.order_by("numero")
        ]
        esperada = [
            (int(item["numero"]), item["vencimento"], Decimal(str(item["valor"])))
            for item in parcelas
        ]
        if conflito or estrutura != esperada:
            raise ValidationError(
                {"chave_idempotencia": "Conflito: a chave ja existe com payload financeiro diferente."}
            )
        return existente

    exigir_competencia_gerencial_aberta(
        matriz=matriz,
        data_competencia=data_competencia,
    )

    titulo = criar_titulo_financeiro(
        matriz=matriz,
        loja=loja,
        natureza=natureza,
        origem_tipo=TituloFinanceiro.OrigemTipo.MANUAL,
        origem_id=chave_idempotencia,
        chave_idempotencia=chave_idempotencia,
        descricao=descricao,
        data_emissao=data_emissao,
        parcelas=parcelas,
        usuario=usuario,
        request=request,
    )
    if titulo.valor_original != valor_final:
        raise ValidationError({"valor_final": "O valor final deve coincidir com o total das parcelas."})
    titulo.plano_conta = plano_conta
    titulo.centro_custo = centro_custo
    titulo.entidade_nome = entidade_nome
    titulo.documento_referencia = documento_referencia
    titulo.data_competencia = data_competencia
    titulo.valor_bruto = valor_bruto
    titulo.valor_desconto = valor_desconto
    titulo.valor_juros = valor_juros
    titulo.observacao = observacao
    titulo.full_clean()
    titulo.save(update_fields=[
        "plano_conta", "centro_custo", "entidade_nome", "documento_referencia",
        "data_competencia", "valor_bruto", "valor_desconto", "valor_juros",
        "observacao", "atualizado_em",
    ])
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
    total_estornado_baixa = sum(
        (evento.valor for evento in eventos if evento.baixa_estornada_id == baixa_original.pk),
        Decimal("0.00"),
    )
    saldo_estornavel_baixa = baixa_original.valor - total_estornado_baixa
    if valor > saldo_estornavel_baixa:
        raise ValidationError({"valor": "O estorno nao pode exceder o saldo estornavel da baixa."})

    estorno = BaixaFinanceira(
        parcela=parcela,
        baixa_estornada=baixa_original,
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
def atualizar_lancamento_manual(
    *, titulo, loja, natureza, descricao, data_emissao, parcelas, plano_conta,
    centro_custo=None, entidade_nome="", documento_referencia="",
    data_competencia=None, valor_bruto=None, valor_desconto=Decimal("0.00"),
    valor_juros=Decimal("0.00"), observacao="", usuario=None, request=None,
):
    if not usuario_tem_permissao(usuario, PERMISSAO_FINANCEIRO_EDITAR_LANCAMENTO):
        raise PermissionDenied("Usuario sem permissao para editar lancamentos financeiros.")
    titulo = TituloFinanceiro.objects.select_for_update().get(pk=titulo.pk)
    _exigir_escopo_titulo_financeiro(usuario=usuario, titulo=titulo)
    if titulo.origem_tipo not in {
        TituloFinanceiro.OrigemTipo.MANUAL,
        TituloFinanceiro.OrigemTipo.AJUSTE,
    }:
        raise ValidationError("Somente lancamentos manuais ou de ajuste podem ser corrigidos por este fluxo.")
    if titulo.status != TituloFinanceiro.Status.ABERTO:
        raise ValidationError("Somente titulos abertos podem ser corrigidos.")
    if titulo.parcelas.filter(baixas__isnull=False).exists():
        raise ValidationError("Titulo com baixa financeira nao pode ser corrigido diretamente.")
    if titulo.data_competencia:
        exigir_competencia_gerencial_aberta(matriz=titulo.matriz, data_competencia=titulo.data_competencia)
    if data_competencia:
        exigir_competencia_gerencial_aberta(matriz=titulo.matriz, data_competencia=data_competencia)
    if loja is not None and loja.matriz_id != titulo.matriz_id:
        raise ValidationError({"loja": "A loja deve pertencer a mesma matriz do titulo."})
    if loja is not None and loja.pk != titulo.loja_id:
        titulo_destino = type(titulo)(matriz_id=titulo.matriz_id, loja_id=loja.pk)
        _exigir_escopo_titulo_financeiro(usuario=usuario, titulo=titulo_destino)
    if plano_conta is not None and plano_conta.matriz_id != titulo.matriz_id:
        raise ValidationError({"plano_conta": "O plano de contas deve pertencer a mesma matriz do titulo."})
    if centro_custo is not None and centro_custo.matriz_id != titulo.matriz_id:
        raise ValidationError({"centro_custo": "O centro de custo deve pertencer a mesma matriz do titulo."})
    parcelas = list(parcelas)
    if not parcelas:
        raise ValidationError({"parcelas": "Informe ao menos uma parcela."})
    numeros_parcelas = [i["numero"] for i in parcelas]
    if len(numeros_parcelas) != len(set(numeros_parcelas)):
        raise ValidationError({"parcelas": "Os numeros das parcelas devem ser unicos."})

    valores_parcelas = [Decimal(str(i["valor"])) for i in parcelas]
    if any(valor <= Decimal("0.00") for valor in valores_parcelas):
        raise ValidationError({"parcelas": "O valor de cada parcela deve ser maior que zero."})

    total = sum(valores_parcelas, Decimal("0.00"))
    bruto = Decimal(str(valor_bruto if valor_bruto is not None else total))
    desconto = Decimal(str(valor_desconto or 0))
    juros = Decimal(str(valor_juros or 0))
    final = bruto - desconto + juros
    if bruto <= Decimal("0.00") or final <= Decimal("0.00"):
        raise ValidationError({"valor_bruto": "O valor do lancamento deve ser maior que zero."})
    if total != final:
        raise ValidationError({"parcelas": "A soma das parcelas deve ser igual ao valor final do titulo."})
    antes = {"natureza": titulo.natureza, "loja_id": titulo.loja_id,
             "plano_conta_id": titulo.plano_conta_id, "centro_custo_id": titulo.centro_custo_id,
             "data_competencia": titulo.data_competencia.isoformat() if titulo.data_competencia else None,
             "valor_bruto": str(titulo.valor_bruto) if titulo.valor_bruto is not None else None}
    titulo.loja=loja; titulo.natureza=natureza; titulo.descricao=descricao
    titulo.data_emissao=data_emissao; titulo.plano_conta=plano_conta; titulo.centro_custo=centro_custo
    titulo.entidade_nome=entidade_nome; titulo.documento_referencia=documento_referencia
    titulo.data_competencia=data_competencia; titulo.valor_bruto=bruto
    titulo.valor_desconto=desconto; titulo.valor_juros=juros; titulo.valor_original=final
    titulo.observacao=observacao
    titulo.save(update_fields=["loja","natureza","descricao","data_emissao","plano_conta","centro_custo",
        "entidade_nome","documento_referencia","data_competencia","valor_bruto","valor_desconto",
        "valor_juros","valor_original","observacao","atualizado_em"])
    titulo.parcelas.all().delete()
    for item in parcelas:
        ParcelaFinanceira.objects.create(titulo=titulo, numero=item["numero"],
            vencimento=item["vencimento"], valor_original=Decimal(str(item["valor"])),
            status=ParcelaFinanceira.Status.ABERTO)
    depois = {"natureza": titulo.natureza, "loja_id": titulo.loja_id,
              "plano_conta_id": titulo.plano_conta_id, "centro_custo_id": titulo.centro_custo_id,
              "data_competencia": titulo.data_competencia.isoformat() if titulo.data_competencia else None,
              "valor_bruto": str(titulo.valor_bruto)}
    registrar_auditoria(matriz=titulo.matriz, loja=titulo.loja, usuario=usuario, acao=RegistroAuditoria.ACAO_EDITAR,
        recurso="financeiro.titulo", recurso_id=str(titulo.uuid),
        descricao=f"Lancamento manual corrigido. Antes={antes}; Depois={depois}.", request=request)
    return titulo


@transaction.atomic
def cancelar_titulo_financeiro(*, titulo, usuario=None, request=None, motivo=None):
    if not usuario_tem_permissao(usuario, PERMISSAO_FINANCEIRO_CANCELAR_LANCAMENTO):
        raise PermissionDenied("Usuario sem permissao para cancelar lancamentos financeiros.")
    titulo = TituloFinanceiro.objects.select_for_update().get(pk=titulo.pk)
    _exigir_escopo_titulo_financeiro(usuario=usuario, titulo=titulo)

    if titulo.status == TituloFinanceiro.Status.CANCELADO:
        return titulo

    if titulo.origem_tipo not in {
        TituloFinanceiro.OrigemTipo.MANUAL,
        TituloFinanceiro.OrigemTipo.AJUSTE,
    }:
        raise ValidationError(
            {"titulo": "Titulos de origem automatica devem ser corrigidos no processo de origem."}
        )

    motivo = (motivo or "").strip()
    if not motivo:
        raise ValidationError({"motivo": "O motivo do cancelamento e obrigatorio."})

    if titulo.data_competencia is not None:
        exigir_competencia_gerencial_aberta(matriz=titulo.matriz, data_competencia=titulo.data_competencia)

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
        descricao=f"Titulo financeiro cancelado: uuid={titulo.uuid}; motivo={motivo}.",
        request=request,
    )
    return titulo

@transaction.atomic
def registrar_baixa_financeira_com_caixa(
    *, parcela, valor, data, chave_idempotencia, forma_pagamento,
    conta_financeira=None, sessao_caixa=None, operador=None,
    observacao="", usuario=None, request=None
):
    from pdv.choices import TipoFormaPagamento, TipoMovimentacaoCaixa
    from pdv.services.vendas.caixa import registrar_movimentacao_caixa_operacional

    titulo = parcela.titulo
    if forma_pagamento.matriz_id != titulo.matriz_id:
        raise ValidationError({"forma_pagamento": "Forma de pagamento de outra matriz."})
    dinheiro = forma_pagamento.tipo == TipoFormaPagamento.DINHEIRO
    if dinheiro:
        if conta_financeira is not None:
            raise ValidationError({"conta_financeira": "Baixa em dinheiro nao utiliza conta financeira."})
        if sessao_caixa is None or operador is None:
            raise ValidationError({"sessao_caixa": "Dinheiro exige sessao aberta e operador."})
        if titulo.loja_id is None:
            raise ValidationError({"loja": "Titulo sem loja nao pode ser baixado em dinheiro."})
        if sessao_caixa.caixa.matriz_id != titulo.matriz_id or sessao_caixa.caixa.loja_id != titulo.loja_id:
            raise ValidationError({"sessao_caixa": "Sessao incompatível com matriz/loja do titulo."})
    else:
        if conta_financeira is None:
            raise ValidationError({"conta_financeira": "Conta financeira e obrigatoria para baixa nao-dinheiro."})
        if conta_financeira.matriz_id != titulo.matriz_id:
            raise ValidationError({"conta_financeira": "Conta financeira de outra matriz."})
        if not conta_financeira.ativo:
            raise ValidationError({"conta_financeira": "Conta financeira inativa."})
        if conta_financeira.loja_id is not None and titulo.loja_id is not None and conta_financeira.loja_id != titulo.loja_id:
            raise ValidationError({"conta_financeira": "Conta financeira de outra loja."})

    baixa = registrar_baixa_financeira(
        parcela=parcela, valor=valor, data=data,
        chave_idempotencia=chave_idempotencia, observacao=observacao,
        usuario=usuario, request=request,
    )
    if baixa.forma_pagamento_id not in (None, forma_pagamento.pk):
        raise ValidationError({"chave_idempotencia": "Baixa existente usa outra forma de pagamento."})
    if baixa.forma_pagamento_id is None:
        baixa.forma_pagamento=forma_pagamento
    if not dinheiro:
        if baixa.conta_financeira_id not in (None, conta_financeira.pk):
            raise ValidationError({"chave_idempotencia": "Baixa existente usa outra conta financeira."})
        if baixa.conta_financeira_id is None:
            baixa.conta_financeira=conta_financeira
        baixa.save(update_fields=["forma_pagamento", "conta_financeira"])
        return baixa
    baixa.save(update_fields=["forma_pagamento"])
    if baixa.movimentacao_caixa_id is None:
        tipo = TipoMovimentacaoCaixa.SANGRIA if titulo.natureza == TituloFinanceiro.Natureza.PAGAR else TipoMovimentacaoCaixa.SUPRIMENTO
        movimento = registrar_movimentacao_caixa_operacional(
            sessao_caixa=sessao_caixa, tipo=tipo, valor=baixa.valor,
            operador=operador, descricao=f"Financeiro: {titulo.descricao}",
        )
        baixa.sessao_caixa=sessao_caixa
        baixa.movimentacao_caixa=movimento
        baixa.save(update_fields=["sessao_caixa","movimentacao_caixa"])
    elif baixa.sessao_caixa_id != sessao_caixa.pk:
        raise ValidationError({"chave_idempotencia": "Baixa existente vinculada a outra sessao."})
    return baixa


@transaction.atomic
def estornar_baixa_financeira_com_caixa(
    *, baixa, valor, data, chave_idempotencia, operador=None,
    observacao="", usuario=None, request=None
):
    from pdv.choices import TipoFormaPagamento, TipoMovimentacaoCaixa
    from pdv.services.vendas.caixa import registrar_movimentacao_caixa_operacional

    original = (
        BaixaFinanceira.objects.select_for_update()
        .select_related("forma_pagamento","sessao_caixa","movimentacao_caixa","parcela__titulo")
        .get(pk=baixa.pk)
    )
    estorno = estornar_baixa_financeira(
        baixa=original, valor=valor, data=data,
        chave_idempotencia=chave_idempotencia, observacao=observacao,
        usuario=usuario, request=request,
    )
    dinheiro = original.forma_pagamento_id is not None and original.forma_pagamento.tipo == TipoFormaPagamento.DINHEIRO
    if not dinheiro:
        if estorno.forma_pagamento_id not in (None, original.forma_pagamento_id):
            raise ValidationError({"chave_idempotencia": "Estorno existente usa outra forma de pagamento."})
        if estorno.conta_financeira_id not in (None, original.conta_financeira_id):
            raise ValidationError({"chave_idempotencia": "Estorno existente usa outra conta financeira."})
        estorno.forma_pagamento=original.forma_pagamento
        estorno.conta_financeira=original.conta_financeira
        estorno.save(update_fields=["forma_pagamento", "conta_financeira"])
        return estorno
    if operador is None:
        raise ValidationError({"operador": "Estorno em dinheiro exige operador."})
    if original.movimentacao_caixa_id is None or original.sessao_caixa_id is None:
        raise ValidationError({"baixa": "Baixa em dinheiro sem movimento de caixa rastreavel."})
    if estorno.movimentacao_caixa_id is None:
        movimento = registrar_movimentacao_caixa_operacional(
            sessao_caixa=original.sessao_caixa,
            tipo=TipoMovimentacaoCaixa.ESTORNO,
            valor=estorno.valor, operador=operador,
            movimentacao_estornada=original.movimentacao_caixa,
            descricao=f"Estorno financeiro: {original.parcela.titulo.descricao}",
        )
        estorno.forma_pagamento=original.forma_pagamento
        estorno.sessao_caixa=original.sessao_caixa
        estorno.movimentacao_caixa=movimento
        estorno.save(update_fields=["forma_pagamento","sessao_caixa","movimentacao_caixa"])
    return estorno


def competencia_gerencial_esta_fechada(*, matriz, data_competencia):
    if matriz is None or data_competencia is None:
        return False
    return FechamentoGerencial.objects.filter(matriz=matriz, competencia_ano=data_competencia.year, competencia_mes=data_competencia.month, status=FechamentoGerencial.Status.FECHADO).exists()


def exigir_competencia_gerencial_aberta(*, matriz, data_competencia):
    if competencia_gerencial_esta_fechada(matriz=matriz, data_competencia=data_competencia):
        raise ValidationError({"data_competencia": "A competencia gerencial esta fechada. Reabra a competencia antes de alterar fatos economicos."})


def validar_fechamento_gerencial(*, matriz, competencia_ano, competencia_mes):
    erros = []
    itens = []
    matriz_valida = matriz is not None and getattr(matriz, "pk", None) is not None
    itens.append({"codigo":"MATRIZ_VALIDA","status":"OK" if matriz_valida else "PENDENTE","bloqueante":True})
    if not matriz_valida: erros.append("Matriz obrigatoria.")
    ano_valido = isinstance(competencia_ano, int) and not isinstance(competencia_ano, bool) and competencia_ano >= 1
    itens.append({"codigo":"COMPETENCIA_ANO_VALIDA","status":"OK" if ano_valido else "PENDENTE","bloqueante":True})
    if not ano_valido: erros.append("Ano de competencia invalido.")
    mes_valido = isinstance(competencia_mes, int) and not isinstance(competencia_mes, bool) and 1 <= competencia_mes <= 12
    itens.append({"codigo":"COMPETENCIA_MES_VALIDA","status":"OK" if mes_valido else "PENDENTE","bloqueante":True})
    if not mes_valido: erros.append("Mes de competencia invalido.")
    if matriz_valida and ano_valido and mes_valido:
        from calendar import monthrange
        from datetime import date
        inicio=date(competencia_ano,competencia_mes,1)
        fim=date(competencia_ano,competencia_mes,monthrange(competencia_ano,competencia_mes)[1])
        economicos=TituloFinanceiro.objects.filter(matriz=matriz,origem_tipo__in=[TituloFinanceiro.OrigemTipo.MANUAL,TituloFinanceiro.OrigemTipo.AJUSTE],data_competencia__range=(inicio,fim)).exclude(status=TituloFinanceiro.Status.CANCELADO)
        sem_classificacao=economicos.filter(
            Q(plano_conta__isnull=True)
            | (
                Q(plano_conta__natureza__in=[PlanoConta.Natureza.DESPESA, PlanoConta.Natureza.RECEITA])
                & (Q(plano_conta__classificacao_dre__isnull=True) | Q(plano_conta__classificacao_dre=""))
            )
        ).count()
        class_ok=sem_classificacao==0
        itens.append({"codigo":"LANCAMENTOS_ECONOMICOS_CLASSIFICADOS_DRE","status":"OK" if class_ok else "PENDENTE","bloqueante":True,"quantidade":sem_classificacao})
        if not class_ok: erros.append("Existem lancamentos economicos ativos sem classificacao DRE explicita.")
        from configuracoes.models import FechamentoComissao
        comissao_existe=FechamentoComissao.objects.filter(matriz=matriz,competencia_ano=competencia_ano,competencia_mes=competencia_mes).exists()
        itens.append({"codigo":"COMISSAO_MENSAL","status":"OK" if comissao_existe else "AVISO","bloqueante":False,"quantidade":1 if comissao_existe else 0})
        from pdv.models import ItemVenda
        itens_venda=ItemVenda.objects.filter(venda__matriz=matriz,venda__finalizada_em__date__range=(inicio,fim),venda__cancelada_em__isnull=True)
        if any(f.name=="cancelado" for f in ItemVenda._meta.fields): itens_venda=itens_venda.filter(cancelado=False)
        snapshot_zero=itens_venda.filter(custo_unitario_snapshot=0).count()
        itens.append({"codigo":"INTEGRIDADE_CMV_SNAPSHOT","status":"AVISO" if snapshot_zero else "OK","bloqueante":False,"quantidade":snapshot_zero})
    pendencias=[item for item in itens if item["status"]=="PENDENTE"]
    avisos=[item for item in itens if item["status"]=="AVISO"]
    return {"valido":not any(item["bloqueante"] for item in pendencias),"erros":erros,"pendencias":pendencias,"avisos":avisos,"itens":itens}

@transaction.atomic
def fechar_competencia_gerencial(*, matriz, competencia_ano, competencia_mes, usuario, request=None):
    validacao = validar_fechamento_gerencial(matriz=matriz, competencia_ano=competencia_ano, competencia_mes=competencia_mes)
    if not validacao["valido"]:
        raise ValidationError({"fechamento_gerencial": validacao["erros"]})
    if usuario is None or getattr(usuario, "pk", None) is None:
        raise ValidationError({"usuario": "Usuario responsavel pelo fechamento e obrigatorio."})
    fechamento, _ = FechamentoGerencial.objects.select_for_update().get_or_create(
        matriz=matriz, competencia_ano=competencia_ano, competencia_mes=competencia_mes,
        defaults={"status": FechamentoGerencial.Status.ABERTO},
    )
    if fechamento.status == FechamentoGerencial.Status.FECHADO:
        return fechamento
    fechamento.status = FechamentoGerencial.Status.FECHADO
    fechamento.fechado_por = usuario
    fechamento.fechado_em = timezone.now()
    fechamento.save(update_fields=["status","fechado_por","fechado_em","atualizado_em"])
    registrar_auditoria(usuario=usuario, matriz=matriz, loja=None, acao=RegistroAuditoria.ACAO_EDITAR,
        recurso="financeiro.fechamento_gerencial", recurso_id=fechamento.uuid,
        descricao=f"Competencia gerencial fechada: {competencia_mes:02d}/{competencia_ano}.", request=request)
    return fechamento


@transaction.atomic
def reabrir_competencia_gerencial(*, fechamento, usuario, motivo, request=None):
    if not usuario_tem_permissao(usuario, PERMISSAO_FINANCEIRO_REABRIR_COMPETENCIA):
        raise PermissionDenied("Usuario sem permissao para reabrir competencia gerencial.")
    if not getattr(usuario, "is_superuser", False) and getattr(usuario, "perfil", None) not in {"master", "admin_loja"}:
        raise PermissionDenied("Reabertura de competencia restrita a perfil administrativo.")
    if usuario is None or getattr(usuario, "pk", None) is None:
        raise ValidationError({"usuario": "Usuario responsavel pela reabertura e obrigatorio."})
    motivo=(motivo or "").strip()
    if not motivo:
        raise ValidationError({"motivo": "O motivo da reabertura e obrigatorio."})
    fechamento=FechamentoGerencial.objects.select_for_update().get(pk=fechamento.pk)
    if fechamento.status == FechamentoGerencial.Status.ABERTO:
        raise ValidationError({"fechamento_gerencial": "A competencia ja esta aberta."})
    fechamento.status=FechamentoGerencial.Status.ABERTO
    fechamento.reaberto_por=usuario
    fechamento.reaberto_em=timezone.now()
    fechamento.motivo_reabertura=motivo
    fechamento.save(update_fields=["status","reaberto_por","reaberto_em","motivo_reabertura","atualizado_em"])
    registrar_auditoria(usuario=usuario, matriz=fechamento.matriz, loja=None, acao=RegistroAuditoria.ACAO_EDITAR,
        recurso="financeiro.fechamento_gerencial", recurso_id=fechamento.uuid,
        descricao=f"Competencia gerencial reaberta: {fechamento.competencia_mes:02d}/{fechamento.competencia_ano}; motivo={motivo}.",
        request=request)
    return fechamento
