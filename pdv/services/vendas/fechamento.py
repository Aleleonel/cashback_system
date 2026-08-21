from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError
from django.db import transaction

from cashback.services import executar_venda_idempotente
from pdv.choices import StatusOperacaoVenda, TipoFormaPagamento
from pdv.models import FormaPagamento, PagamentoVenda, Venda
from pdv.services.vendas.finalizacao import finalizar_venda
from pdv.services.vendas.beneficios import resolver_beneficio_da_venda

CENTAVOS = Decimal("0.01")


def _decimal(valor, campo):
    try:
        return Decimal(str(valor or "0").replace(",", ".")).quantize(CENTAVOS)
    except (InvalidOperation, ValueError):
        raise ValidationError({campo: "Informe um valor monetÃ¡rio vÃ¡lido."})


def garantir_formas_pagamento_basicas(*, matriz):
    padroes = (
        ("DINHEIRO", "Dinheiro", TipoFormaPagamento.DINHEIRO, False, 1, True),
        ("PIX", "PIX", TipoFormaPagamento.PIX, False, 1, False),
        ("CREDITO", "CartÃ£o de crÃ©dito", TipoFormaPagamento.CARTAO_CREDITO, True, 12, False),
        ("DEBITO", "CartÃ£o de dÃ©bito", TipoFormaPagamento.CARTAO_DEBITO, False, 1, False),
    )
    for codigo, nome, tipo, parcelamento, maximo, troco in padroes:
        FormaPagamento.objects.get_or_create(
            matriz=matriz,
            codigo=codigo,
            defaults={
                "nome": nome,
                "tipo": tipo,
                "ativa": True,
                "permite_parcelamento": parcelamento,
                "maximo_parcelas": maximo,
                "movimenta_caixa": True,
                "permite_troco": troco,
            },
        )
    return FormaPagamento.objects.filter(matriz=matriz, ativa=True).order_by("nome")


def serializar_formas_pagamento(*, matriz):
    return [
        {
            "id": forma.pk,
            "nome": forma.nome,
            "tipo": forma.tipo,
            "permite_parcelamento": forma.permite_parcelamento,
            "maximo_parcelas": forma.maximo_parcelas,
            "permite_troco": forma.permite_troco,
            "exige_autorizacao": forma.exige_autorizacao,
        }
        for forma in garantir_formas_pagamento_basicas(matriz=matriz)
    ]



def _registrar_beneficio(venda, usuario, tipo, cashback, voucher):
    cliente = venda.cliente
    identificado = cliente is not None and cliente.cpf != "CONSUMIDOR"

    if tipo != "nenhum" and not identificado:
        raise ValidationError(
            {"cliente": "Identifique o cliente para utilizar benefÃ­cios."}
        )

    beneficio_resolvido = resolver_beneficio_da_venda(
        matriz=venda.matriz,
        loja=venda.loja,
        cliente=venda.cliente,
        valor_compra=venda.total,
        tipo_beneficio=tipo,
        valor_cashback=cashback,
        codigo_voucher=voucher,
    )

    if not identificado:
        return beneficio_resolvido.valor

    resultado = executar_venda_idempotente(
        matriz=venda.matriz,
        loja=venda.loja,
        usuario=usuario,
        chave_idempotencia=venda.uuid,
        cpf=cliente.cpf,
        nome=cliente.nome,
        telefone=cliente.telefone or "",
        email=cliente.email or "",
        data_nascimento=cliente.data_nascimento,
        valor_compra=venda.total,
        valor_cashback_usado=(
            cashback if tipo == "cashback" else Decimal("0.00")
        ),
        aceita_email=cliente.aceita_email,
        aceita_sms=cliente.aceita_sms,
        observacao=f"Venda PDV {venda.pk}.",
        aplicar_voucher=tipo == "voucher",
        codigo_voucher=voucher if tipo == "voucher" else "",
    )

    beneficios = resultado.beneficios or {}

    if tipo == "voucher":
        valor_persistido = Decimal(
            beneficios.get("desconto_voucher") or 0
        ).quantize(CENTAVOS)
    elif tipo == "cashback":
        valor_persistido = Decimal(
            beneficios.get("cashback_usado") or 0
        ).quantize(CENTAVOS)
    else:
        valor_persistido = Decimal("0.00")

    if valor_persistido != beneficio_resolvido.valor:
        raise ValidationError(
            {
                "beneficio": (
                    "DivergÃªncia no cÃ¡lculo do benefÃ­cio: "
                    f"adaptador={beneficio_resolvido.valor} e "
                    f"persistÃªncia={valor_persistido}."
                )
            }
        )

    return beneficio_resolvido.valor





def _registrar_pagamentos(venda, pagamentos):
    if not isinstance(pagamentos, list) or not pagamentos:
        raise ValidationError({"pagamentos": "Informe ao menos um pagamento."})

    venda.pagamentos.all().delete()
    soma = Decimal("0.00")

    for indice, dados in enumerate(pagamentos, 1):
        try:
            forma = FormaPagamento.objects.get(
                pk=dados.get("forma_pagamento_id"),
                matriz=venda.matriz,
                ativa=True,
            )
        except FormaPagamento.DoesNotExist:
            raise ValidationError({"pagamentos": f"Forma invÃ¡lida na linha {indice}."})

        if forma.exige_autorizacao:
            raise ValidationError({"pagamentos": f"{forma.nome} exige autorizaÃ§Ã£o."})

        valor = _decimal(dados.get("valor"), "pagamentos")
        parcelas = int(dados.get("parcelas") or 1)
        recebido = None
        troco = Decimal("0.00")

        if valor <= 0:
            raise ValidationError({"pagamentos": "Os pagamentos devem ser positivos."})

        if forma.permite_troco:
            recebido = _decimal(dados.get("valor_recebido") or valor, "valor_recebido")
            troco = (recebido - valor).quantize(CENTAVOS)

        pagamento = PagamentoVenda(
            venda=venda,
            forma_pagamento=forma,
            valor=valor,
            parcelas=parcelas,
            valor_recebido=recebido,
            troco=troco,
        )
        pagamento.full_clean()
        pagamento.save()
        soma += valor

    soma = soma.quantize(CENTAVOS)
    if soma != venda.total:
        raise ValidationError({
            "pagamentos": f"A soma dos pagamentos ({soma}) deve ser igual ao total ({venda.total})."
        })


@transaction.atomic
def fechar_venda_web(
    *,
    venda,
    usuario,
    pagamentos,
    tipo_emissao="nao_fiscal",
    uf_destino="",
    tipo_beneficio="nenhum",
    valor_cashback="0",
    codigo_voucher="",
    request=None,
):
    venda = Venda.objects.select_for_update().select_related(
        "matriz", "loja", "cliente", "operador", "vendedor"
    ).get(pk=venda.pk)

    if venda.status == StatusOperacaoVenda.FINALIZADA:
        return venda

    venda.tipo_emissao = (tipo_emissao or "nao_fiscal").strip()
    venda.uf_destino = (uf_destino or "").strip().upper()

    if tipo_beneficio not in {"nenhum", "voucher", "cashback"}:
        raise ValidationError({"beneficio": "Escolha um benefÃ­cio vÃ¡lido."})

    cashback = _decimal(valor_cashback, "cashback")
    if tipo_beneficio != "cashback":
        cashback = Decimal("0.00")
    if tipo_beneficio == "voucher" and not codigo_voucher:
        raise ValidationError({"voucher": "Informe o voucher escolhido."})

    venda.recalcular_totais()
    desconto = _registrar_beneficio(
        venda, usuario, tipo_beneficio, cashback, codigo_voucher
    )

    venda.desconto_geral = desconto
    venda.status = StatusOperacaoVenda.PAGAMENTO
    venda.recalcular_totais(salvar=False)
    venda.full_clean()
    venda.save(update_fields=[
        "tipo_emissao", "uf_destino", "desconto_geral", "desconto", "total",
        "status", "atualizada_em"
    ])

    _registrar_pagamentos(venda, pagamentos)

    venda_finalizada = finalizar_venda(
        venda=venda,
        usuario=usuario,
        request=request,
    )


    return venda_finalizada
