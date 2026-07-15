from django.db.models import Q

from produtos.models import Marca


def get_marcas(
    *,
    matriz,
    busca='',
    somente_ativas=False,
):
    marcas = Marca.objects.filter(
        matriz=matriz
    ).select_related(
        'matriz'
    ).order_by(
        'nome'
    )

    if somente_ativas:
        marcas = marcas.filter(
            ativa=True
        )

    busca = (busca or '').strip()

    if busca:
        marcas = marcas.filter(
            Q(nome__icontains=busca)
            | Q(fabricante__icontains=busca)
        )

    return marcas


def get_marca(
    *,
    matriz,
    marca_id,
):
    return Marca.objects.select_related(
        'matriz'
    ).get(
        matriz=matriz,
        id=marca_id
    )
