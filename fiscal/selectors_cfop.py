from django.db.models import Q
from fiscal.models import CFOP


def get_cfops(*, busca="", somente_ativos=False, tipo_operacao="", destino_operacao=""):
    registros = CFOP.objects.all().order_by("codigo")

    if somente_ativos:
        registros = registros.filter(ativo=True)
    if tipo_operacao:
        registros = registros.filter(tipo_operacao=tipo_operacao)
    if destino_operacao:
        registros = registros.filter(destino_operacao=destino_operacao)

    busca = (busca or "").strip()
    if busca:
        if len(busca) == 4 and busca.isdigit():
            registros = registros.filter(codigo=busca)
        else:
            registros = registros.filter(
                Q(codigo__icontains=busca) | Q(descricao__icontains=busca)
            )

    return registros


def get_cfop(*, cfop_id):
    return CFOP.objects.get(id=cfop_id)
