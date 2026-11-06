from django.core.exceptions import ValidationError
from django.utils import timezone
from atacado.models import ModeloFiscalPedidoAtacado, TipoEmissaoPedidoAtacado

def configurar_emissao_pedido_atacado(*, pedido, tipo_emissao, uf_destino=""):
    if tipo_emissao not in TipoEmissaoPedidoAtacado.values:
        raise ValidationError({"tipo_emissao": "Tipo de emissao invalido."})
    uf=str(uf_destino or "").strip().upper()
    pedido.tipo_emissao=tipo_emissao
    if tipo_emissao == TipoEmissaoPedidoAtacado.FISCAL:
        if not pedido.loja_id:
            raise ValidationError({"loja": "Pedido fiscal de atacado exige loja emissora."})
        if len(uf) != 2:
            raise ValidationError({"uf_destino_fiscal": "Informe a UF de destino."})
        pedido.modelo_fiscal=ModeloFiscalPedidoAtacado.NFE
        pedido.uf_destino_fiscal=uf
        pedido.fiscal_solicitado_em=timezone.now()
    else:
        pedido.modelo_fiscal=""
        pedido.uf_destino_fiscal=""
        pedido.fiscal_solicitado_em=None
    pedido.full_clean()
    pedido.save(update_fields=["tipo_emissao","modelo_fiscal","uf_destino_fiscal","fiscal_solicitado_em"])
    return pedido
