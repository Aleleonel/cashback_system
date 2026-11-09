"""F32P3C: guardas de contexto para futura consolidacao Atacado/PDV.

Nao finaliza pedidos, nao cria vendas e nao movimenta estoque/caixa.
"""
from django.core.exceptions import ValidationError
from pdv.choices import StatusSessaoCaixa
from pdv.models import SessaoCaixa
from .models import StatusPedidoAtacado


def validar_contexto_consolidacao(*, pedido, sessao_caixa, operador):
    """Valida pedido, sessao aberta e escopo da loja/matriz.

    Retorna a sessao atualizada do banco. Sem efeitos colaterais.
    A autorizacao operacional fina ainda devera ser validada na camada HTTP.
    """
    if pedido.status != StatusPedidoAtacado.GERADO:
        raise ValidationError({"pedido": "Somente pedido gerado pode ser consolidado."})
    if pedido.venda_pdv_id:
        raise ValidationError({"pedido": "Pedido ja vinculado a uma venda PDV."})
    if not pedido.loja_id:
        raise ValidationError({"loja": "Pedido deve possuir loja operacional."})
    if not pedido.vendedor_id:
        raise ValidationError({"vendedor": "Pedido deve possuir vendedor."})
    if operador is None or not getattr(operador, "pk", None) or not getattr(operador, "is_active", False):
        raise ValidationError({"operador": "Informe um operador ativo e autenticado."})
    if sessao_caixa is None or not getattr(sessao_caixa, "pk", None):
        raise ValidationError({"sessao_caixa": "Informe uma sessao de caixa aberta."})
    sessao = SessaoCaixa.objects.select_related("caixa", "caixa__loja").get(pk=sessao_caixa.pk)
    if sessao.status != StatusSessaoCaixa.ABERTA:
        raise ValidationError({"sessao_caixa": "A sessao deve estar aberta."})
    if sessao.caixa.loja_id != pedido.loja_id:
        raise ValidationError({"sessao_caixa": "A sessao deve pertencer a loja do pedido."})
    if sessao.caixa.loja.matriz_id != pedido.matriz_id:
        raise ValidationError({"sessao_caixa": "A sessao deve pertencer a matriz do pedido."})
    return sessao
