from django.core.exceptions import ValidationError
from django.db import transaction

from produtos.models import Categoria

from .auditoria import auditar_criacao, auditar_edicao


def _normalizar_nome(nome):
    return (nome or '').strip()


def _validar_nome_categoria(
    *,
    matriz,
    nome,
    categoria_excluida=None,
):
    nome = _normalizar_nome(nome)

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


@transaction.atomic
def criar_categoria(
    *,
    matriz,
    dados,
    usuario_executor,
    loja=None,
    request=None,
):
    nome = _validar_nome_categoria(
        matriz=matriz,
        nome=dados.get('nome'),
    )

    categoria = Categoria.objects.create(
        matriz=matriz,
        nome=nome,
        descricao=(dados.get('descricao') or '').strip(),
        ativa=dados.get('ativa', True),
    )

    auditar_criacao(
        recurso='produtos.categoria',
        instancia=categoria,
        usuario_executor=usuario_executor,
        matriz=matriz,
        loja=loja,
        descricao=f'Categoria criada: {categoria.nome}',
        request=request,
    )

    return categoria


@transaction.atomic
def editar_categoria(
    *,
    categoria,
    dados,
    usuario_executor,
    loja=None,
    request=None,
):
    nome = _validar_nome_categoria(
        matriz=categoria.matriz,
        nome=dados.get('nome'),
        categoria_excluida=categoria,
    )

    categoria.nome = nome
    categoria.descricao = (
        dados.get('descricao') or ''
    ).strip()
    categoria.ativa = dados.get(
        'ativa',
        categoria.ativa,
    )

    categoria.full_clean()
    categoria.save(
        update_fields=[
            'nome',
            'descricao',
            'ativa',
            'atualizada_em',
        ]
    )

    auditar_edicao(
        recurso='produtos.categoria',
        instancia=categoria,
        usuario_executor=usuario_executor,
        matriz=categoria.matriz,
        loja=loja,
        descricao=f'Categoria atualizada: {categoria.nome}',
        request=request,
    )

    return categoria
