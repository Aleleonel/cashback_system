from django.core.exceptions import ValidationError
from django.db import transaction

from auditoria.models import RegistroAuditoria
from auditoria.services import registrar_auditoria
from produtos.models import (
    Categoria,
    Marca,
    Produto,
    UnidadeMedida,
)
from produtos.services import (
    criar_produto,
    editar_produto,
)


def _obter_relacionamento(
    *,
    modelo,
    matriz,
    objeto_id,
    obrigatorio=False,
    nome_campo,
):
    if not objeto_id:
        if obrigatorio:
            raise ValidationError({
                nome_campo: (
                    f'{nome_campo.replace("_", " ").title()} '
                    'não informado.'
                )
            })

        return None

    try:
        return modelo.objects.get(
            id=objeto_id,
            matriz=matriz,
        )
    except modelo.DoesNotExist as erro:
        raise ValidationError({
            nome_campo: (
                f'{nome_campo.replace("_", " ").title()} '
                'não encontrado na matriz atual.'
            )
        }) from erro


def _montar_dados_produto(
    *,
    matriz,
    linha,
):
    categoria = _obter_relacionamento(
        modelo=Categoria,
        matriz=matriz,
        objeto_id=linha.get('categoria_id'),
        obrigatorio=False,
        nome_campo='categoria',
    )

    marca = _obter_relacionamento(
        modelo=Marca,
        matriz=matriz,
        objeto_id=linha.get('marca_id'),
        obrigatorio=False,
        nome_campo='marca',
    )

    unidade_medida = _obter_relacionamento(
        modelo=UnidadeMedida,
        matriz=matriz,
        objeto_id=linha.get('unidade_medida_id'),
        obrigatorio=True,
        nome_campo='unidade_medida',
    )

    return {
        'categoria': categoria,
        'marca': marca,
        'unidade_medida': unidade_medida,
        'codigo_interno': linha.get(
            'codigo_interno',
            ''
        ),
        'sku': linha.get(
            'sku',
            ''
        ),
        'gtin': linha.get(
            'gtin',
            ''
        ),
        'ncm': linha.get(
            'ncm',
            ''
        ),
        'nome': linha.get(
            'nome',
            ''
        ),
        'descricao': linha.get(
            'descricao',
            ''
        ),
        'custo_base': linha.get(
            'custo_base',
            '0.00'
        ),
        'preco_venda': linha.get(
            'preco_venda',
            '0.00'
        ),
        'origem_preco': linha.get(
            'origem_preco',
            'manual'
        ),
        'peso_liquido_gramas': linha.get(
            'peso_liquido_gramas'
        ),
        'peso_bruto_gramas': linha.get(
            'peso_bruto_gramas'
        ),
        'altura_cm': (
            linha.get('altura_cm')
            or None
        ),
        'largura_cm': (
            linha.get('largura_cm')
            or None
        ),
        'comprimento_cm': (
            linha.get('comprimento_cm')
            or None
        ),
        'controla_estoque': linha.get(
            'controla_estoque',
            True
        ),
        'estoque_minimo': linha.get(
            'estoque_minimo',
            '0.000'
        ),
        'status': linha.get(
            'produto_status',
            'ativo'
        ),
    }


def _obter_produto_existente(
    *,
    matriz,
    linha,
):
    produto_id = linha.get(
        'produto_id'
    )

    if not produto_id:
        return None

    try:
        return Produto.objects.get(
            id=produto_id,
            matriz=matriz,
        )
    except Produto.DoesNotExist as erro:
        raise ValidationError({
            'produto': (
                'O produto que seria atualizado não existe '
                'mais ou não pertence à matriz atual.'
            )
        }) from erro


def validar_linhas_para_confirmacao(
    linhas,
):
    if not linhas:
        raise ValidationError(
            'Nenhuma linha pendente para importação.'
        )

    linhas_invalidas = [
        linha
        for linha in linhas
        if not linha.get('valido')
    ]

    if linhas_invalidas:
        raise ValidationError(
            (
                'A importação possui linhas inválidas. '
                'Corrija a planilha e faça uma nova validação.'
            )
        )


@transaction.atomic
def executar_importacao_produtos(
    *,
    matriz,
    loja,
    linhas,
    usuario_executor,
    request=None,
):
    validar_linhas_para_confirmacao(
        linhas
    )

    criados = 0
    atualizados = 0

    for linha in linhas:
        dados = _montar_dados_produto(
            matriz=matriz,
            linha=linha,
        )

        produto_existente = _obter_produto_existente(
            matriz=matriz,
            linha=linha,
        )

        if produto_existente is None:
            criar_produto(
                matriz=matriz,
                dados=dados,
                usuario_executor=usuario_executor,
                loja=loja,
                request=request,
            )

            criados += 1
            continue

        editar_produto(
            produto=produto_existente,
            dados=dados,
            usuario_executor=usuario_executor,
            loja=loja,
            request=request,
        )

        atualizados += 1

    resultado = {
        'total': criados + atualizados,
        'criados': criados,
        'atualizados': atualizados,
    }

    registrar_auditoria(
        usuario=usuario_executor,
        matriz=matriz,
        loja=loja,
        acao=RegistroAuditoria.ACAO_IMPORTAR,
        recurso='produtos.importacao',
        descricao=(
            'Importação de produtos concluída. '
            f'Criados: {criados}. '
            f'Atualizados: {atualizados}.'
        ),
        request=request,
    )

    return resultado
