from decimal import Decimal

from django.core.exceptions import ValidationError

from pdv.choices import (
    StatusOperacaoVenda,
    StatusSessaoCaixa,
    TipoEmissaoVenda,
    TipoOperacaoVenda,
)


STATUS_FINALIZAVEIS = {
    StatusOperacaoVenda.RASCUNHO,
    StatusOperacaoVenda.ABERTA,
    StatusOperacaoVenda.PAGAMENTO,
}


def validar_venda_para_finalizacao(*, venda, permitir_fiscal=False):
    errors = {}

    if venda.tipo_operacao != TipoOperacaoVenda.VENDA:
        errors["tipo_operacao"] = "Somente uma operacao de venda pode ser finalizada."

    if venda.status not in STATUS_FINALIZAVEIS:
        errors["status"] = "A venda nao esta em um status permitido para finalizacao."

    if not venda.operador_id:
        errors["operador"] = "Informe o operador responsavel pela venda."

    if not venda.vendedor_id:
        errors["vendedor"] = "Informe o vendedor responsavel pela venda."
    else:
        vendedor = venda.vendedor
        if hasattr(vendedor, "ativo") and not vendedor.ativo:
            errors["vendedor"] = "O vendedor informado esta inativo."
        if getattr(vendedor, "matriz_id", None) != venda.matriz_id:
            errors["vendedor"] = "O vendedor deve pertencer a mesma matriz da venda."

    sessao = venda.sessao_caixa
    if sessao is None:
        errors["sessao_caixa"] = "A venda deve estar vinculada a uma sessao de caixa."
    elif sessao.status != StatusSessaoCaixa.ABERTA:
        errors["sessao_caixa"] = "A sessao de caixa deve estar aberta."
    elif sessao.caixa.loja_id != venda.loja_id:
        errors["sessao_caixa"] = "A sessao de caixa deve pertencer a loja da venda."

    if not venda.cliente_id:
        errors["cliente"] = "Informe o cliente ou associe o cliente padrao CONSUMIDOR."

    if venda.tipo_emissao == TipoEmissaoVenda.FISCAL and not permitir_fiscal:
        errors["tipo_emissao"] = (
            "A emissao fiscal ainda nao esta disponivel na release nao fiscal."
        )

    itens = list(
        venda.itens.filter(cancelado=False)
        .select_related("produto")
        .order_by("sequencia")
    )
    if not itens:
        errors["itens"] = "A venda deve possuir pelo menos um item ativo."

    venda.recalcular_totais(salvar=False)
    if venda.total <= Decimal("0.00"):
        errors["total"] = "O total da venda deve ser maior que zero."

    pagamentos = list(
        venda.pagamentos.select_related("forma_pagamento").order_by("criado_em")
    )
    if not pagamentos:
        errors["pagamentos"] = "A venda deve possuir pelo menos um pagamento."
    else:
        total_pagamentos = Decimal("0.00")
        for pagamento in pagamentos:
            if not pagamento.forma_pagamento.ativa:
                errors["pagamentos"] = "A venda possui forma de pagamento inativa."
                break
            try:
                pagamento.full_clean()
            except ValidationError as exc:
                errors["pagamentos"] = exc.message_dict
                break
            total_pagamentos += pagamento.valor

        total_pagamentos = total_pagamentos.quantize(Decimal("0.01"))
        if "pagamentos" not in errors and total_pagamentos != venda.total:
            errors["pagamentos"] = (
                f"A soma dos pagamentos ({total_pagamentos}) deve ser igual "
                f"ao total da venda ({venda.total})."
            )

    if errors:
        raise ValidationError(errors)

    return venda
