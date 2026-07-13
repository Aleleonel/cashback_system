from django.db import transaction

from produtos.models import Categoria
from produtos.services.auditoria import auditar_criacao

from .validacoes import validar_nome_categoria


@transaction.atomic
def criar_categoria(
    *,
    matriz,
    dados,
    usuario_executor,
    loja=None,
    request=None,
):
    nome = validar_nome_categoria(
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
