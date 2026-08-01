from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction

from pdv.choices import StatusSessaoCaixa, TipoMovimentacaoCaixa
from pdv.models import MovimentacaoCaixa, Venda


def calcular_valor_movimenta_caixa(*, venda):
    total = Decimal("0.00")

    pagamentos = (
        venda.pagamentos
        .select_related("forma_pagamento")
        .filter(forma_pagamento__movimenta_caixa=True)
        .order_by("criado_em")
    )

    for pagamento in pagamentos:
        total += pagamento.valor

    return total.quantize(Decimal("0.01"))


@transaction.atomic
def registrar_movimentacao_caixa_venda(*, venda, operador):
    venda = (
        Venda.objects
        .select_for_update()
        .select_related("sessao_caixa")
        .get(pk=venda.pk)
    )

    sessao = venda.sessao_caixa
    if sessao is None:
        raise ValidationError({
            "sessao_caixa": "A venda deve possuir uma sessao de caixa."
        })

    if sessao.status != StatusSessaoCaixa.ABERTA:
        raise ValidationError({
            "sessao_caixa": "A sessao de caixa deve estar aberta."
        })

    valor = calcular_valor_movimenta_caixa(venda=venda)

    existente = (
        MovimentacaoCaixa.objects
        .select_for_update()
        .filter(
            venda=venda,
            tipo=TipoMovimentacaoCaixa.VENDA,
        )
        .first()
    )

    if existente is not None:
        if (
            existente.sessao_caixa_id != sessao.pk
            or existente.valor != valor
        ):
            raise ValidationError({
                "movimentacao_caixa": (
                    "Ja existe uma movimentacao de caixa incompatível "
                    "para esta venda."
                )
            })
        return existente

    if valor <= Decimal("0.00"):
        return None

    movimentacao = MovimentacaoCaixa(
        sessao_caixa=sessao,
        tipo=TipoMovimentacaoCaixa.VENDA,
        valor=valor,
        operador=operador,
        venda=venda,
        descricao=f"Recebimento da venda {venda.uuid}.",
    )
    movimentacao.full_clean()
    movimentacao.save()

    return movimentacao


# PDV-04F.1.1 - ABERTURA SEGURA DE CAIXA
@transaction.atomic
def abrir_sessao_caixa(*, caixa, operador, valor_abertura, observacao=""):
    from django.contrib.auth import get_user_model
    from pdv.models import Caixa, MovimentacaoCaixa, SessaoCaixa

    valor_abertura = Decimal(str(valor_abertura)).quantize(Decimal("0.01"))
    if valor_abertura < Decimal("0.00"):
        raise ValidationError("O valor de abertura nao pode ser negativo.")

    usuario = (
        get_user_model().objects
        .select_for_update()
        .get(pk=operador.pk)
    )
    caixa = (
        Caixa.objects
        .select_for_update()
        .select_related("matriz", "loja")
        .get(pk=caixa.pk)
    )

    existente_operador = (
        SessaoCaixa.objects
        .select_for_update()
        .select_related("caixa")
        .filter(
            operador_abertura=usuario,
            status=StatusSessaoCaixa.ABERTA,
        )
        .order_by("aberta_em", "id")
        .first()
    )
    if existente_operador is not None:
        raise ValidationError(
            "O operador ja possui uma sessao de caixa aberta: "
            f"{existente_operador.caixa.nome}."
        )

    existente_caixa = (
        SessaoCaixa.objects
        .select_for_update()
        .filter(
            caixa=caixa,
            status=StatusSessaoCaixa.ABERTA,
        )
        .first()
    )
    if existente_caixa is not None:
        raise ValidationError("Este caixa ja possui uma sessao aberta.")

    sessao = SessaoCaixa(
        caixa=caixa,
        operador_abertura=usuario,
        valor_abertura=valor_abertura,
        observacao_abertura=(observacao or "").strip(),
    )
    sessao.full_clean()
    sessao.save()

    if valor_abertura > Decimal("0.00"):
        movimento = MovimentacaoCaixa(
            sessao_caixa=sessao,
            tipo=TipoMovimentacaoCaixa.ABERTURA,
            valor=valor_abertura,
            operador=usuario,
            descricao="Abertura da sessao de caixa.",
        )
        movimento.full_clean()
        movimento.save()

    return sessao

# PDV-04C.1 - FECHAMENTO DE CAIXA
def calcular_saldo_sessao_caixa(*, sessao):
    # Calcula o saldo esperado usando apenas movimentos persistidos.
    from decimal import Decimal
    from pdv.choices import TipoMovimentacaoCaixa
    from pdv.models import MovimentacaoCaixa

    positivos = {
        TipoMovimentacaoCaixa.ABERTURA,
        TipoMovimentacaoCaixa.VENDA,
        TipoMovimentacaoCaixa.SUPRIMENTO,
    }
    negativos = {
        TipoMovimentacaoCaixa.SANGRIA,
        TipoMovimentacaoCaixa.ESTORNO,
    }

    total = Decimal("0.00")
    movimentos = MovimentacaoCaixa.objects.filter(
        sessao_caixa=sessao
    ).exclude(tipo=TipoMovimentacaoCaixa.FECHAMENTO)

    for movimento in movimentos.only("tipo", "valor"):
        if movimento.tipo in positivos:
            total += movimento.valor
        elif movimento.tipo in negativos:
            total -= movimento.valor

    return total.quantize(Decimal("0.01"))


def fechar_sessao_caixa(*, sessao_id, operador, valor_informado, observacao=""):
    # Fecha a sessao de forma atomica e rejeita reprocessamento.
    from decimal import Decimal
    from django.core.exceptions import ValidationError
    from django.db import transaction
    from pdv.choices import (
        StatusOperacaoVenda,
        StatusSessaoCaixa,
        TipoMovimentacaoCaixa,
    )
    from pdv.models import MovimentacaoCaixa, SessaoCaixa, Venda

    valor_informado = Decimal(str(valor_informado)).quantize(Decimal("0.01"))
    if valor_informado < 0:
        raise ValidationError("O valor informado nao pode ser negativo.")

    with transaction.atomic():
        sessao = (
            SessaoCaixa.objects.select_for_update()
            .select_related("caixa", "caixa__loja")
            .get(pk=sessao_id)
        )

        if sessao.status != StatusSessaoCaixa.ABERTA:
            raise ValidationError("Esta sessao de caixa nao esta aberta.")

        vendas_pendentes = (
            Venda.objects.filter(sessao_caixa=sessao)
            .exclude(
                status__in=[
                    StatusOperacaoVenda.FINALIZADA,
                    StatusOperacaoVenda.CANCELADA,
                ]
            )
            .exists()
        )
        if vendas_pendentes:
            raise ValidationError(
                "Existem vendas pendentes. Finalize ou cancele antes de fechar o caixa."
            )

        valor_calculado = calcular_saldo_sessao_caixa(sessao=sessao)
        diferenca = (valor_informado - valor_calculado).quantize(Decimal("0.01"))

        sessao.status = StatusSessaoCaixa.FECHADA
        sessao.operador_fechamento = operador
        sessao.valor_fechamento_informado = valor_informado
        sessao.valor_fechamento_calculado = valor_calculado
        sessao.diferenca_fechamento = diferenca
        sessao.observacao_fechamento = (observacao or "").strip()

        update_fields = [
            "status",
            "operador_fechamento",
            "valor_fechamento_informado",
            "valor_fechamento_calculado",
            "diferenca_fechamento",
            "observacao_fechamento",
        ]

        for candidate in ("fechada_em", "encerrada_em", "fechamento_em"):
            if any(field.name == candidate for field in SessaoCaixa._meta.fields):
                from django.utils import timezone
                setattr(sessao, candidate, timezone.now())
                update_fields.append(candidate)
                break

        sessao.save(update_fields=update_fields)

        field_names = {field.name for field in MovimentacaoCaixa._meta.fields}
        kwargs = {
            "sessao_caixa": sessao,
            "tipo": TipoMovimentacaoCaixa.FECHAMENTO,
            "valor": valor_informado,
        }
        optional = {
            "caixa": sessao.caixa,
            "operador": operador,
            "usuario": operador,
            "descricao": (
                "Fechamento de caixa. "
                f"Calculado={valor_calculado}; informado={valor_informado}; "
                f"diferenca={diferenca}."
            ),
            "observacao": (observacao or "").strip(),
            "matriz": getattr(sessao.caixa, "matriz", None),
            "loja": getattr(sessao.caixa, "loja", None),
        }
        for name, value in optional.items():
            if name in field_names and value is not None:
                kwargs[name] = value

        movimento = None
        if valor_calculado > Decimal("0.00"):
            movimento = MovimentacaoCaixa.objects.create(**kwargs)

        movimento_id = (
            movimento.pk
            if movimento is not None
            else "nao_gerado_saldo_zero"
        )

        try:
            from auditoria.models import RegistroAuditoria
            from auditoria.services import registrar_auditoria

            registrar_auditoria(
                usuario=operador,
                acao=RegistroAuditoria.ACAO_EDITAR,
                recurso="sessao_caixa",
                recurso_id=str(sessao.pk),
                descricao=(
                    "Fechamento de caixa: "
                    f"calculado={valor_calculado}; informado={valor_informado}; "
                    f"diferenca={diferenca}; movimento={movimento_id}."
                ),
                matriz=getattr(operador, "matriz", None),
                loja=getattr(operador, "loja", None),
            )
        except TypeError:
            # Mantem a operacao compativel com assinaturas antigas de auditoria.
            registrar_auditoria(
                usuario=operador,
                acao=RegistroAuditoria.ACAO_EDITAR,
                recurso="sessao_caixa",
                recurso_id=str(sessao.pk),
                descricao=(
                    "Fechamento de caixa: "
                    f"calculado={valor_calculado}; informado={valor_informado}; "
                    f"diferenca={diferenca}."
                ),
            )

        return sessao
