from django.db import transaction

from produtos.models import UnidadeMedida
from produtos.services.auditoria import auditar_criacao

from .validacoes import (
    validar_descricao_unidade,
    validar_sigla_unidade,
)


@transaction.atomic
def criar_unidade_medida(
    *,
    matriz,
    dados,
    usuario_executor,
    loja=None,
    request=None,
):
    sigla = validar_sigla_unidade(
        matriz=matriz,
        sigla=dados.get('sigla'),
    )

    descricao = validar_descricao_unidade(
        dados.get('descricao')
    )

    unidade = UnidadeMedida.objects.create(
        matriz=matriz,
        sigla=sigla,
        descricao=descricao,
        ativa=dados.get('ativa', True),
    )

    auditar_criacao(
        recurso='produtos.unidade_medida',
        instancia=unidade,
        usuario_executor=usuario_executor,
        matriz=matriz,
        loja=loja,
        descricao=(
            f'Unidade de medida criada: '
            f'{unidade.sigla} - {unidade.descricao}'
        ),
        request=request,
    )

    return unidade
