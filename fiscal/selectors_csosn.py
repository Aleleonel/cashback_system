from django.db.models import Q
from fiscal.models import CSOSN

def get_csosns(*, busca="", somente_ativos=False):
    csts = CSOSN.objects.all().order_by("codigo")

    if somente_ativos:
        csts = csts.filter(ativo=True)

    busca = (busca or "").strip()

    if busca:
        if len(busca) == 3 and busca.isdigit():
            csts = csts.filter(codigo=busca)
        else:
            csts = csts.filter(
                Q(codigo__icontains=busca)
                | Q(descricao__icontains=busca)
            )

    return csts

def get_csosn(*, csosn_id):
    return CSOSN.objects.get(id=csosn_id)
