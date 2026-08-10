from decimal import Decimal

from django.core.exceptions import ValidationError

from fiscal.domain.calculo_tributario import (
    ContextoCalculoTributario,
)
from fiscal.selectors_configuracao_fiscal import (
    get_configuracao_fiscal_matriz,
)
from fiscal.services_contexto_tributario import (
    construir_contexto_tributario,
)
from fiscal.services_motor_tributario import calcular_tributos
from pdv.choices import TipoEmissaoVenda
from pdv.services.fiscal.snapshot_venda import (
    consolidar_dados_venda_fiscal,
    construir_dados_item_venda_fiscal,
    persistir_item_venda_fiscal,
    persistir_venda_fiscal,
)
from produtos.services.fiscal.resolver_produto_fiscal import (
    resolver_produto_fiscal,
)


ZERO = Decimal("0")


def _validar_venda_fiscal(*, venda):
    erros = {}

    if venda.tipo_emissao != TipoEmissaoVenda.FISCAL:
        erros["tipo_emissao"] = (
            "A orquestracao fiscal exige uma venda fiscal."
        )

    if venda.matriz_id is None:
        erros["matriz"] = "Informe a matriz da venda."

    if venda.loja_id is None:
        erros["loja"] = "Informe a loja da venda."

    if not (venda.uf_destino or "").strip():
        erros["uf_destino"] = (
            "Informe a UF de destino para a venda fiscal."
        )

    if erros:
        raise ValidationError(erros)


def _construir_contexto_item(*, venda, item):
    return construir_contexto_tributario(
        matriz=venda.matriz,
        loja=venda.loja,
        produto=item.produto,
        uf_destino=venda.uf_destino,
        contribuinte_icms=None,
        consumidor_final=None,
    )


def _resolver_item_fiscal(*, item, contexto_tributario):
    resolvido = resolver_produto_fiscal(
        produto=item.produto,
        contexto=contexto_tributario,
    )

    if not resolvido.valido:
        detalhe = "; ".join(
            str(alerta)
            for alerta in resolvido.alertas
            if alerta
        )

        mensagem = (
            f"O item {item.sequencia} nao possui "
            "configuracao fiscal apta."
        )

        if detalhe:
            mensagem = f"{mensagem} {detalhe}"

        raise ValidationError({"fiscal": mensagem})

    if resolvido.resultado_selecao_fiscal is None:
        raise ValidationError({
            "fiscal": (
                f"O item {item.sequencia} nao possui "
                "resultado de selecao fiscal."
            )
        })

    return resolvido


def _construir_contexto_calculo(*, item, resolvido):
    contexto = ContextoCalculoTributario(
        resultado_selecao_fiscal=(
            resolvido.resultado_selecao_fiscal
        ),
        valor_produtos=Decimal(item.subtotal),
        quantidade=Decimal(item.quantidade),
        desconto=Decimal(item.desconto),
        acrescimo=Decimal(item.acrescimo),
        frete=ZERO,
        seguro=ZERO,
        outras_despesas=ZERO,
        valor_unitario=Decimal(item.preco_unitario),
        valor_item=Decimal(item.total),
        informacoes_adicionais={
            "item_venda_id": item.pk,
            "sequencia": item.sequencia,
            "venda_id": item.venda_id,
        },
    )

    return contexto.validar()


def preparar_e_persistir_snapshot_fiscal_venda(*, venda):
    _validar_venda_fiscal(venda=venda)

    configuracao = get_configuracao_fiscal_matriz(
        matriz=venda.matriz,
    )

    if configuracao is None:
        raise ValidationError({
            "configuracao_fiscal": (
                "A matriz nao possui configuracao fiscal ativa."
            )
        })

    if not configuracao.pronta_para_operacao:
        raise ValidationError({
            "configuracao_fiscal": (
                "A configuracao fiscal da matriz esta incompleta."
            )
        })

    itens = list(
        venda.itens
        .filter(cancelado=False)
        .select_related("produto")
        .order_by("sequencia")
    )

    if not itens:
        raise ValidationError({
            "itens": "A venda precisa possuir ao menos um item ativo."
        })

    snapshots_itens = []
    contexto_venda = None

    for item in itens:
        contexto_tributario = _construir_contexto_item(
            venda=venda,
            item=item,
        )

        if contexto_venda is None:
            contexto_venda = contexto_tributario

        resolvido = _resolver_item_fiscal(
            item=item,
            contexto_tributario=contexto_tributario,
        )

        contexto_calculo = _construir_contexto_calculo(
            item=item,
            resolvido=resolvido,
        )

        resultado_calculo = calcular_tributos(
            contexto_calculo
        )

        dados_item = construir_dados_item_venda_fiscal(
            item_venda=item,
            contexto_tributario=contexto_tributario,
            contexto_calculo=contexto_calculo,
            produto_fiscal=resolvido,
            resultado_calculo=resultado_calculo,
            configuracao_fiscal_id_original=configuracao.pk,
        )

        snapshot_item = persistir_item_venda_fiscal(
            item_venda=item,
            dados=dados_item,
        )

        snapshots_itens.append(snapshot_item)

    dados_venda = consolidar_dados_venda_fiscal(
        venda=venda,
        contexto_tributario=contexto_venda,
        snapshots_itens=snapshots_itens,
        configuracao_fiscal_id_original=configuracao.pk,
    )

    return persistir_venda_fiscal(
        venda=venda,
        dados=dados_venda,
    )