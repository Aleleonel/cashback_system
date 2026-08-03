from django.db.models import Q

from fiscal.models import NCM


def get_ncms(*, busca="", somente_ativos=False):
    registros = NCM.objects.all().order_by("codigo")

    if somente_ativos:
        registros = registros.filter(ativo=True)

    busca = (busca or "").strip()

    if busca:
        codigo_busca = NCM.normalizar_codigo(busca)

        if len(codigo_busca) == 8:
            registros = registros.filter(codigo=codigo_busca)
        else:
            registros = registros.filter(
                Q(codigo__icontains=busca)
                | Q(descricao__icontains=busca)
            )

    return registros


def get_ncm(*, ncm_id):
    return NCM.objects.get(id=ncm_id)
