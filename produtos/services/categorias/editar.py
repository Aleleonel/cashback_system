from django.db import transaction

from produtos.services.auditoria import auditar_edicao

from .validacoes import validar_nome_categoria


@transaction.atomic
def editar_categoria(
    *,
    categoria,
    dados,
    usuario_executor,
    loja=None,
    request=None,
):
    nome = validar_nome_categoria(
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
