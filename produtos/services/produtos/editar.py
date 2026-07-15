from django.db import transaction

from produtos.services.auditoria import auditar_edicao

from .validacoes import preparar_dados_produto


CAMPOS_EDITAVEIS = [
    'categoria',
    'marca',
    'unidade_medida',
    'codigo_interno',
    'sku',
    'gtin',
    'ncm',
    'nome',
    'descricao',
    'custo_base',
    'preco_venda',
    'origem_preco',
    'peso_liquido_gramas',
    'peso_bruto_gramas',
    'altura_cm',
    'largura_cm',
    'comprimento_cm',
    'controla_estoque',
    'estoque_minimo',
    'status',
]


@transaction.atomic
def editar_produto(
    *,
    produto,
    dados,
    usuario_executor,
    loja=None,
    request=None,
):
    dados_completos = {
        campo: getattr(produto, campo)
        for campo in CAMPOS_EDITAVEIS
    }

    dados_completos.update(dados)

    dados_validados = preparar_dados_produto(
        matriz=produto.matriz,
        dados=dados_completos,
        produto_excluido=produto,
    )

    for campo, valor in dados_validados.items():
        setattr(produto, campo, valor)

    produto.full_clean()

    produto.save(
        update_fields=[
            *CAMPOS_EDITAVEIS,
            'atualizado_em',
        ]
    )

    auditar_edicao(
        recurso='produtos.produto',
        instancia=produto,
        usuario_executor=usuario_executor,
        matriz=produto.matriz,
        loja=loja,
        descricao=(
            f'Produto atualizado: '
            f'{produto.codigo_interno} - {produto.nome}'
        ),
        request=request,
    )

    return produto
