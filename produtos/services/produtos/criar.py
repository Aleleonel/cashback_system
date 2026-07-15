from django.db import transaction

from produtos.models import Produto
from produtos.services.auditoria import auditar_criacao

from .validacoes import preparar_dados_produto


@transaction.atomic
def criar_produto(
    *,
    matriz,
    dados,
    usuario_executor,
    loja=None,
    request=None,
):
    dados_validados = preparar_dados_produto(
        matriz=matriz,
        dados=dados,
    )

    produto = Produto.objects.create(
        matriz=matriz,
        **dados_validados,
    )

    auditar_criacao(
        recurso='produtos.produto',
        instancia=produto,
        usuario_executor=usuario_executor,
        matriz=matriz,
        loja=loja,
        descricao=(
            f'Produto criado: '
            f'{produto.codigo_interno} - {produto.nome}'
        ),
        request=request,
    )

    return produto
