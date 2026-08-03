from django.db.models import Q

from fiscal.models import CEST


def get_cests(
    *,
    busca="",
    somente_ativos=False,
    segmento="",
):
    registros = CEST.objects.all().order_by("codigo")

    if somente_ativos:
        registros = registros.filter(ativo=True)

    segmento = (segmento or "").strip()
    if segmento:
        registros = registros.filter(
            segmento__icontains=segmento,
        )

    busca = (busca or "").strip()
    if busca:
        codigo = CEST.normalizar_codigo(busca)
        if len(codigo) == 7:
            registros = registros.filter(codigo=codigo)
        else:
            registros = registros.filter(
                Q(descricao__icontains=busca)
                | Q(segmento__icontains=busca)
                | Q(ncm_referencia__icontains=codigo)
                | Q(excecao__icontains=busca)
            )

    return registros


def get_cest(*, cest_id):
    return CEST.objects.get(id=cest_id)
