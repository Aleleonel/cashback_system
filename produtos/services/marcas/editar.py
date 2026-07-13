from django.db import transaction

from produtos.services.auditoria import auditar_edicao

from .validacoes import validar_nome_marca


@transaction.atomic
def editar_marca(
    *,
    marca,
    dados,
    usuario_executor,
    loja=None,
    request=None,
):
    nome = validar_nome_marca(
        matriz=marca.matriz,
        nome=dados.get('nome'),
        marca_excluida=marca,
    )

    marca.nome = nome
    marca.fabricante = (
        dados.get('fabricante') or ''
    ).strip()
    marca.ativa = dados.get(
        'ativa',
        marca.ativa,
    )

    marca.full_clean()
    marca.save(
        update_fields=[
            'nome',
            'fabricante',
            'ativa',
            'atualizada_em',
        ]
    )

    auditar_edicao(
        recurso='produtos.marca',
        instancia=marca,
        usuario_executor=usuario_executor,
        matriz=marca.matriz,
        loja=loja,
        descricao=f'Marca atualizada: {marca.nome}',
        request=request,
    )

    return marca
