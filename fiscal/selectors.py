from django.db.models import Q

from fiscal.models import OrigemMercadoria


def get_origens_mercadoria(
    *,
    busca="",
    somente_ativas=False,
):
    origens = OrigemMercadoria.objects.all().order_by("codigo")

    if somente_ativas:
        origens = origens.filter(ativo=True)

    busca = (busca or "").strip()

    if busca:
        if len(busca) == 1 and busca.isdigit():
            origens = origens.filter(codigo=busca)
        else:
            origens = origens.filter(
                Q(codigo__icontains=busca)
                | Q(descricao__icontains=busca)
            )

    return origens


def get_origem_mercadoria(*, origem_id):
    return OrigemMercadoria.objects.get(id=origem_id)

from fiscal.selectors_cst_icms import (
    get_cst_icms,
    get_csts_icms,
)

from fiscal.selectors_csosn import (
    get_csosn,
    get_csosns,
)

from fiscal.selectors_cfop import (
    get_cfop,
    get_cfops,
)

from fiscal.selectors_ncm import (
    get_ncm,
    get_ncms,
)

from fiscal.selectors_cst_pis import (
    get_cst_pis,
    get_csts_pis,
)

from fiscal.selectors_cst_cofins import (
    get_cst_cofins,
    get_csts_cofins,
)

from fiscal.selectors_cst_ipi import (
    get_cst_ipi,
    get_csts_ipi,
)

from fiscal.selectors_cest import (
    get_cest,
    get_cests,
)

from fiscal.selectors_beneficio_fiscal import (
    get_beneficio_fiscal,
    get_beneficios_fiscais,
)

from fiscal.selectors_regra_fiscal import (
    get_regra_fiscal,
    get_regras_ativas_vigentes,
    get_regras_fiscais,
)

from fiscal.services_motor_selecao import (
    RegraFiscalAmbiguaError,
    selecionar_regra_fiscal,
)
