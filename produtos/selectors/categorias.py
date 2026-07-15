from django.db.models import Q

from produtos.models import Categoria


def get_categorias(
    *,
    matriz,
    busca='',
    somente_ativas=False,
):
    categorias = Categoria.objects.filter(
        matriz=matriz
    ).select_related(
        'matriz'
    ).order_by(
        'nome'
    )

    if somente_ativas:
        categorias = categorias.filter(
            ativa=True
        )

    busca = (busca or '').strip()

    if busca:
        categorias = categorias.filter(
            Q(nome__icontains=busca)
            | Q(descricao__icontains=busca)
        )

    return categorias


def get_categoria(
    *,
    matriz,
    categoria_id,
):
    return Categoria.objects.select_related(
        'matriz'
    ).get(
        matriz=matriz,
        id=categoria_id
    )
