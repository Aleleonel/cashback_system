from django.db import transaction

from produtos.models import Marca
from produtos.services.auditoria import auditar_criacao

from .validacoes import validar_nome_marca


@transaction.atomic
def criar_marca(
    *,
    matriz,
    dados,
    usuario_executor,
    loja=None,
    request=None,
):
    nome = validar_nome_marca(
        matriz=matriz,
        nome=dados.get('nome'),
    )

    marca = Marca.objects.create(
        matriz=matriz,
        nome=nome,
        fabricante=(dados.get('fabricante') or '').strip(),
        ativa=dados.get('ativa', True),
    )

    auditar_criacao(
        recurso='produtos.marca',
        instancia=marca,
        usuario_executor=usuario_executor,
        matriz=matriz,
        loja=loja,
        descricao=f'Marca criada: {marca.nome}',
        request=request,
    )

    return marca
