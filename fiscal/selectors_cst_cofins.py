from django.db.models import Q

from fiscal.models import CSTCOFINS


def get_csts_cofins(*, busca="", somente_ativos=False, tipo_operacao=""):
    registros = CSTCOFINS.objects.all().order_by("codigo")

    if somente_ativos:
        registros = registros.filter(ativo=True)

    if tipo_operacao:
        registros = registros.filter(tipo_operacao=tipo_operacao)

    busca = (busca or "").strip()

    if busca:
        if len(busca) == 2 and busca.isdigit():
            registros = registros.filter(codigo=busca)
        else:
            registros = registros.filter(
                Q(codigo__icontains=busca)
                | Q(descricao__icontains=busca)
            )

    return registros


def get_cst_cofins(*, cst_cofins_id):
    return CSTCOFINS.objects.get(id=cst_cofins_id)
