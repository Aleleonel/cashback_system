from django.core.exceptions import ValidationError

from produtos.models import Marca


def normalizar_nome_marca(nome):
    return (nome or '').strip()


def validar_nome_marca(
    *,
    matriz,
    nome,
    marca_excluida=None,
):
    nome = normalizar_nome_marca(nome)

    if not nome:
        raise ValidationError({
            'nome': 'Informe o nome da marca.'
        })

    marcas = Marca.objects.filter(
        matriz=matriz,
        nome__iexact=nome,
    )

    if marca_excluida is not None:
        marcas = marcas.exclude(
            id=marca_excluida.id
        )

    if marcas.exists():
        raise ValidationError({
            'nome': 'Já existe uma marca com este nome.'
        })

    return nome
