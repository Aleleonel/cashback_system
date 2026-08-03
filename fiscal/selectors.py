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
