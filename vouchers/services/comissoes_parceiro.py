from decimal import Decimal, ROUND_HALF_UP
from django.db import transaction
from vouchers.models import ComissaoParceiro, Parceiro, UsoVoucher

CENTAVO=Decimal("0.01")
CEM=Decimal("100")

def _moeda(valor):
    return Decimal(valor).quantize(CENTAVO, rounding=ROUND_HALF_UP)

def _parceiro_elegivel(*, parceiro, data_referencia):
    if not parceiro.ativo: return False
    if parceiro.vigencia_inicio and data_referencia < parceiro.vigencia_inicio: return False
    if parceiro.vigencia_fim and data_referencia > parceiro.vigencia_fim: return False
    return True

@transaction.atomic
def gerar_comissao_parceiro_por_uso(*, uso_voucher):
    uso=(UsoVoucher.objects.select_for_update().select_related("parceiro","matriz").get(pk=uso_voucher.pk))
    existente=ComissaoParceiro.objects.filter(uso_voucher=uso).first()
    if existente is not None: return existente
    parceiro=uso.parceiro
    if parceiro is None or parceiro.matriz_id != uso.matriz_id: return None
    data_referencia=uso.criado_em.date()
    if not _parceiro_elegivel(parceiro=parceiro,data_referencia=data_referencia): return None
    if parceiro.base_calculo == Parceiro.BaseCalculo.BRUTO:
        valor_base=_moeda(uso.valor_compra)
    else:
        valor_base=_moeda(max(Decimal(uso.valor_compra)-Decimal(uso.valor_desconto),Decimal("0.00")))
    percentual=None; valor_fixo=None
    if parceiro.tipo_comissao == Parceiro.TipoComissao.PERCENTUAL:
        percentual=parceiro.percentual_comissao
        valor_comissao=_moeda(valor_base*Decimal(percentual)/CEM)
    elif parceiro.tipo_comissao == Parceiro.TipoComissao.VALOR_FIXO:
        valor_fixo=parceiro.valor_comissao
        valor_comissao=_moeda(valor_fixo)
    else: return None
    return ComissaoParceiro.objects.create(
        uso_voucher=uso,matriz=uso.matriz,parceiro=parceiro,
        tipo_comissao=parceiro.tipo_comissao,base_calculo=parceiro.base_calculo,
        valor_base=valor_base,percentual_aplicado=percentual,
        valor_fixo_aplicado=valor_fixo,valor_comissao=valor_comissao)
