import calendar
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Max
from django.utils import timezone

from estoque.services import confirmar_reserva_estoque
from empresas.models import Loja
from financeiro.models import TituloFinanceiro
from financeiro.services import criar_titulo_financeiro
from pdv.choices import (
    StatusOperacaoVenda,
    TipoEmissaoVenda,
)
from pdv.models import Venda
from pdv.services.fiscal.finalizacao_fiscal import (
    preparar_e_persistir_snapshot_fiscal_venda,
)
from pdv.services.cliente_consumidor import obter_ou_criar_cliente_consumidor

from .auditoria import registrar_auditoria_finalizacao_venda
from .caixa import registrar_movimentacao_caixa_venda
from .estoque import obter_reserva_ativa_item
from .validacoes import validar_venda_para_finalizacao


def _associar_cliente_consumidor(*, venda):
    if venda.cliente_id:
        return venda

    venda.cliente = obter_ou_criar_cliente_consumidor(
        matriz=venda.matriz,
        loja=venda.loja,
    )
    venda.save(update_fields=["cliente", "atualizada_em"])
    return venda


def _confirmar_reservas(*, venda, usuario=None, request=None):
    resultados = []

    itens = (
        venda.itens
        .filter(cancelado=False)
        .select_related("produto")
        .order_by("sequencia")
    )

    for item in itens:
        if not item.produto.controla_estoque:
            continue

        reserva = obter_reserva_ativa_item(item=item)
        if reserva is None:
            raise ValidationError({
                "estoque": (
                    f"O item {item.sequencia} nao possui uma reserva "
                    "de estoque ativa."
                )
            })

        resultado = confirmar_reserva_estoque(
            reserva=reserva,
            usuario=usuario,
            request=request,
        )
        resultados.append(resultado)

    return resultados




def _somar_meses(data_base, meses):
    indice = data_base.month - 1 + meses
    ano = data_base.year + indice // 12
    mes = indice % 12 + 1
    dia = min(data_base.day, calendar.monthrange(ano, mes)[1])
    return data_base.replace(year=ano, month=mes, day=dia)


def _ratear_pagamento_em_parcelas(*, valor, quantidade, primeiro_vencimento):
    valor = Decimal(valor).quantize(Decimal("0.01"))
    quantidade = int(quantidade)
    centavos = int(valor * 100)
    base, resto = divmod(centavos, quantidade)

    parcelas = []
    for indice in range(quantidade):
        valor_centavos = base + (1 if indice < resto else 0)
        parcelas.append({
            "numero": indice + 1,
            "vencimento": _somar_meses(primeiro_vencimento, indice),
            "valor": (Decimal(valor_centavos) / Decimal("100")).quantize(Decimal("0.01")),
        })
    return parcelas


def gerar_contas_receber_venda(*, venda, usuario=None, request=None):
    if not venda.finalizada_em:
        raise ValidationError({
            "financeiro": "A venda deve estar finalizada antes de gerar contas a receber."
        })

    titulos = []
    pagamentos = (
        venda.pagamentos
        .select_related("forma_pagamento")
        .filter(forma_pagamento__gera_contas_receber=True)
        .order_by("criado_em", "pk")
    )

    data_emissao = venda.finalizada_em.date()
    primeiro_vencimento = _somar_meses(data_emissao, 1)

    for pagamento in pagamentos:
        chave_idempotencia = f"venda-pagamento:{pagamento.uuid}"
        parcelas = _ratear_pagamento_em_parcelas(
            valor=pagamento.valor,
            quantidade=pagamento.parcelas,
            primeiro_vencimento=primeiro_vencimento,
        )
        titulo = criar_titulo_financeiro(
            matriz=venda.matriz,
            loja=venda.loja,
            natureza=TituloFinanceiro.Natureza.RECEBER,
            origem_tipo=TituloFinanceiro.OrigemTipo.VENDA_PAGAMENTO,
            origem_id=str(pagamento.uuid),
            chave_idempotencia=chave_idempotencia,
            descricao=f"Venda {venda.uuid} - {pagamento.forma_pagamento.nome}",
            data_emissao=data_emissao,
            parcelas=parcelas,
            usuario=usuario or venda.operador,
            request=request,
        )
        titulos.append(titulo)

    return titulos


# PDV-04E.3.1 - NUMERACAO SEQUENCIAL POR LOJA
def _atribuir_numero_venda(*, venda):
    if venda.numero is not None:
        return venda.numero

    Loja.objects.select_for_update().get(pk=venda.loja_id)

    maior_numero = (
        Venda.objects
        .filter(
            loja_id=venda.loja_id,
            numero__isnull=False,
        )
        .aggregate(maior=Max("numero"))
        ["maior"]
        or 0
    )

    venda.numero = maior_numero + 1
    return venda.numero


def _finalizar_modelo(*, venda):
    _atribuir_numero_venda(venda=venda)
    venda.status = StatusOperacaoVenda.FINALIZADA
    venda.finalizada_em = timezone.now()
    venda.full_clean()
    venda.save(
        update_fields=[
            "cliente",
            "numero",
            "status",
            "finalizada_em",
            "subtotal",
            "desconto",
            "acrescimo",
            "total",
            "quantidade_itens",
            "atualizada_em",
        ]
    )
    return venda


@transaction.atomic
def finalizar_venda(*, venda, usuario=None, request=None):
    venda = (
        Venda.objects
        .select_for_update()
        .select_related(
            "matriz",
            "loja",
            "cliente",
            "operador",
            "vendedor",
            "sessao_caixa",
            "sessao_caixa__caixa",
        )
        .get(pk=venda.pk)
    )

    if venda.status == StatusOperacaoVenda.FINALIZADA:
        return venda

    _associar_cliente_consumidor(venda=venda)
    permitir_fiscal = (
        venda.tipo_emissao == TipoEmissaoVenda.FISCAL
    )

    validar_venda_para_finalizacao(
        venda=venda,
        permitir_fiscal=permitir_fiscal,
    )

    if permitir_fiscal:
        preparar_e_persistir_snapshot_fiscal_venda(
            venda=venda,
        )

    _confirmar_reservas(
        venda=venda,
        usuario=usuario,
        request=request,
    )

    movimentacao_caixa = registrar_movimentacao_caixa_venda(
        venda=venda,
        operador=venda.operador,
    )

    _finalizar_modelo(venda=venda)

    gerar_contas_receber_venda(
        venda=venda,
        usuario=usuario,
        request=request,
    )

    registrar_auditoria_finalizacao_venda(
        venda=venda,
        usuario=usuario or venda.operador,
        movimentacao_caixa=movimentacao_caixa,
        request=request,
    )

    return venda
