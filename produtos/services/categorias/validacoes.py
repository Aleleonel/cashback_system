from django.core.exceptions import ValidationError

from produtos.models import Categoria


def normalizar_nome_categoria(nome):
    return (nome or '').strip()


def validar_nome_categoria(
    *,
    matriz,
    nome,
    categoria_excluida=None,
):
    nome = normalizar_nome_categoria(nome)

    if not nome:
        raise ValidationError({
            'nome': 'Informe o nome da categoria.'
        })

    categorias = Categoria.objects.filter(
        matriz=matriz,
        nome__iexact=nome,
    )

    if categoria_excluida is not None:
        categorias = categorias.exclude(
            id=categoria_excluida.id
        )

    if categorias.exists():
        raise ValidationError({
            'nome': 'Já existe uma categoria com este nome.'
        })

    return nome
