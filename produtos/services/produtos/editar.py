from django.db import transaction
from produtos.models import Produto

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
    'atacado_elegivel',
    'promocional',
    'peso_liquido_gramas',
    'peso_bruto_gramas',
    'altura_cm',
    'largura_cm',
    'comprimento_cm',
    'controla_estoque',
    'estoque_minimo',
    'origem_mercadoria',
    'ncm_fiscal',
    'cest',
    'cst_icms',
    'csosn',
    'cst_pis',
    'cst_cofins',
    'cst_ipi',
    'beneficio_fiscal',
    'regra_fiscal_padrao',
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
    imagem = dados.get('imagem_principal')
    remover_imagem = bool(dados.get('remover_imagem'))
    imagem_anterior = produto.imagem_principal.name if produto.imagem_principal else None
    armazenamento_anterior = produto.imagem_principal.storage if imagem_anterior else None
    # Os dados de imagem nao entram nas validacoes comerciais/fiscais.
    dados = {k: v for k, v in dados.items() if k not in {'imagem_principal', 'remover_imagem'}}
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

    campos_update = [*CAMPOS_EDITAVEIS, 'atualizado_em']
    if remover_imagem:
        produto.imagem_principal = None
        campos_update.append('imagem_principal')
    elif imagem:
        produto.imagem_principal = imagem
        campos_update.append('imagem_principal')

    produto.full_clean()

    produto.save(
        update_fields=campos_update
    )

    imagem_atual = produto.imagem_principal.name if produto.imagem_principal else None
    if imagem_anterior and imagem_anterior != imagem_atual:
        def limpar_imagem_anterior():
            if not Produto.objects.filter(imagem_principal=imagem_anterior).exists():
                armazenamento_anterior.delete(imagem_anterior)
        transaction.on_commit(limpar_imagem_anterior)

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
