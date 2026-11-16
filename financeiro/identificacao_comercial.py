"""Identificação comercial de títulos: apenas leitura, sempre isolada por matriz e loja."""
import uuid
from atacado.models import PedidoAtacado
from financeiro.models import TituloFinanceiro
from pdv.models import PagamentoVenda


def enriquecer_titulos(titulos):
    """Adiciona atributos transitórios a títulos já autorizados; não grava no banco."""
    titulos = list(titulos)
    ids = []
    for titulo in titulos:
        titulo.descricao_comercial = titulo.descricao
        titulo.referencia_comercial = ""
        titulo.forma_comercial = ""
        if titulo.origem_tipo != TituloFinanceiro.OrigemTipo.VENDA_PAGAMENTO:
            continue
        try:
            ids.append(uuid.UUID(str(titulo.origem_id)))
        except (ValueError, TypeError, AttributeError):
            continue
    pagamentos = PagamentoVenda.objects.filter(uuid__in=ids).select_related(
        "venda", "venda__cliente", "forma_pagamento"
    )
    por_uuid = {str(p.uuid): p for p in pagamentos}
    vendas = {p.venda_id for p in pagamentos}
    pedidos = PedidoAtacado.objects.filter(venda_pdv_id__in=vendas).select_related("orcamento_origem")
    por_venda = {p.venda_pdv_id: p for p in pedidos}
    for titulo in titulos:
        if titulo.origem_tipo != TituloFinanceiro.OrigemTipo.VENDA_PAGAMENTO:
            continue
        try:
            pagamento = por_uuid.get(str(uuid.UUID(str(titulo.origem_id))))
        except (ValueError, TypeError, AttributeError):
            continue
        if pagamento is None:
            continue
        venda = pagamento.venda
        # Nunca resolver referência comercial fora do escopo do título.
        if (venda.matriz_id != titulo.matriz_id or venda.loja_id != titulo.loja_id
                or pagamento.forma_pagamento.matriz_id != titulo.matriz_id):
            continue
        pedido = por_venda.get(venda.pk)
        if pedido is not None and (pedido.matriz_id != titulo.matriz_id or pedido.loja_id != titulo.loja_id):
            pedido = None
        cliente = venda.cliente.nome if venda.cliente_id else "Consumidor não identificado"
        numero_venda = str(venda.numero) if venda.numero is not None else str(venda.uuid)[:8]
        if pedido is not None:
            numero_orc = pedido.orcamento_origem.numero
            titulo.descricao_comercial = f"Pedido de atacado nº {pedido.pk} — {cliente}"
            titulo.referencia_comercial = f"Orçamento nº {numero_orc} · Venda nº {numero_venda}"
        else:
            titulo.descricao_comercial = f"Venda nº {numero_venda} — {cliente}"
            titulo.referencia_comercial = f"Venda nº {numero_venda}"
        parcelas = pagamento.parcelas
        titulo.forma_comercial = pagamento.forma_pagamento.nome + (f" · {parcelas} parcelas" if parcelas > 1 else "")
    return titulos
