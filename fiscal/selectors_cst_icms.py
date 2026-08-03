from django.db.models import Q
from fiscal.models import CSTICMS

def get_csts_icms(*, busca="", somente_ativos=False):
    csts = CSTICMS.objects.all().order_by("codigo")
    if somente_ativos:
        csts = csts.filter(ativo=True)
    busca = (busca or "").strip()
    if busca:
        if len(busca) == 2 and busca.isdigit():
            csts = csts.filter(codigo=busca)
        else:
            csts = csts.filter(Q(codigo__icontains=busca) | Q(descricao__icontains=busca))
    return csts

def get_cst_icms(*, cst_id):
    return CSTICMS.objects.get(id=cst_id)
