from django.db.models import Q

from produtos.models import UnidadeMedida


def get_unidades_medida(
    *,
    matriz,
    busca='',
    somente_ativas=False,
):
    unidades = UnidadeMedida.objects.filter(
        matriz=matriz
    ).select_related(
        'matriz'
    ).order_by(
        'sigla'
    )

    if somente_ativas:
        unidades = unidades.filter(
            ativa=True
        )

    busca = (busca or '').strip()

    if busca:
        unidades = unidades.filter(
            Q(sigla__icontains=busca)
            | Q(descricao__icontains=busca)
        )

    return unidades


def get_unidade_medida(
    *,
    matriz,
    unidade_id,
):
    return UnidadeMedida.objects.select_related(
        'matriz'
    ).get(
        matriz=matriz,
        id=unidade_id
    )
