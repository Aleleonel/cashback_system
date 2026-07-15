from django.db import transaction

from produtos.services.auditoria import auditar_edicao

from .validacoes import (
    validar_descricao_unidade,
    validar_sigla_unidade,
)


@transaction.atomic
def editar_unidade_medida(
    *,
    unidade,
    dados,
    usuario_executor,
    loja=None,
    request=None,
):
    sigla = validar_sigla_unidade(
        matriz=unidade.matriz,
        sigla=dados.get('sigla'),
        unidade_excluida=unidade,
    )

    descricao = validar_descricao_unidade(
        dados.get('descricao')
    )

    unidade.sigla = sigla
    unidade.descricao = descricao
    unidade.ativa = dados.get(
        'ativa',
        unidade.ativa,
    )

    unidade.full_clean()
    unidade.save(
        update_fields=[
            'sigla',
            'descricao',
            'ativa',
            'atualizada_em',
        ]
    )

    auditar_edicao(
        recurso='produtos.unidade_medida',
        instancia=unidade,
        usuario_executor=usuario_executor,
        matriz=unidade.matriz,
        loja=loja,
        descricao=(
            f'Unidade de medida atualizada: '
            f'{unidade.sigla} - {unidade.descricao}'
        ),
        request=request,
    )

    return unidade
