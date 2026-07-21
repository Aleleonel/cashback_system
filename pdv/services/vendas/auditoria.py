from auditoria.models import RegistroAuditoria
from auditoria.services import registrar_auditoria


def registrar_auditoria_finalizacao_venda(
    *,
    venda,
    usuario=None,
    movimentacao_caixa=None,
    request=None,
):
    pagamentos = (
        venda.pagamentos
        .select_related("forma_pagamento")
        .order_by("criado_em")
    )

    formas = ", ".join(
        f"{pagamento.forma_pagamento.nome}={pagamento.valor}"
        for pagamento in pagamentos
    )

    quantidade_itens = venda.itens.filter(cancelado=False).count()

    movimento = (
        str(movimentacao_caixa.uuid)
        if movimentacao_caixa is not None
        else "nao_aplicavel"
    )

    return registrar_auditoria(
        usuario=usuario,
        matriz=venda.matriz,
        loja=venda.loja,
        acao=RegistroAuditoria.ACAO_EDITAR,
        recurso="pdv.venda",
        recurso_id=venda.uuid,
        descricao=(
            "Finalizacao de venda: "
            f"uuid={venda.uuid}; "
            f"operador={venda.operador_id}; "
            f"vendedor={venda.vendedor_id}; "
            f"cliente={venda.cliente_id}; "
            f"total={venda.total}; "
            f"itens={quantidade_itens}; "
            f"pagamentos=[{formas}]; "
            f"movimentacao_caixa={movimento}."
        ),
        request=request,
    )
