from django.db.models import Q

from produtos.choices import StatusProduto
from produtos.models import Produto


def get_produtos(
    *,
    matriz,
    busca='',
    status='',
    categoria=None,
    marca=None,
    somente_ativos=False,
):
    produtos = Produto.objects.filter(
        matriz=matriz
    ).select_related(
        'matriz',
        'categoria',
        'marca',
        'unidade_medida',
    ).order_by(
        'nome'
    )

    if somente_ativos:
        produtos = produtos.filter(
            status=StatusProduto.ATIVO
        )
    elif status:
        produtos = produtos.filter(
            status=status
        )

    if categoria:
        produtos = produtos.filter(
            categoria=categoria
        )

    if marca:
        produtos = produtos.filter(
            marca=marca
        )

    busca = (busca or '').strip()

    if busca:
        produtos = produtos.filter(
            Q(nome__icontains=busca)
            | Q(descricao__icontains=busca)
            | Q(codigo_interno__icontains=busca)
            | Q(sku__icontains=busca)
            | Q(gtin__icontains=busca)
            | Q(ncm__icontains=busca)
            | Q(categoria__nome__icontains=busca)
            | Q(marca__nome__icontains=busca)
        )

    return produtos


def get_produto(
    *,
    matriz,
    produto_id,
):
    return Produto.objects.select_related(
        'matriz',
        'categoria',
        'marca',
        'unidade_medida',
    ).get(
        matriz=matriz,
        id=produto_id
    )


def get_produto_por_codigo(
    *,
    matriz,
    codigo,
):
    codigo = (codigo or '').strip()

    if not codigo:
        return None

    return Produto.objects.filter(
        matriz=matriz
    ).select_related(
        'categoria',
        'marca',
        'unidade_medida',
    ).filter(
        Q(codigo_interno__iexact=codigo)
        | Q(sku__iexact=codigo)
        | Q(gtin=codigo)
    ).first()
