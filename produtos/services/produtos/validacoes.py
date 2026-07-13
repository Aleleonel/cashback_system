from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError

from produtos.models import (
    Categoria,
    Marca,
    Produto,
    UnidadeMedida,
)

from .helpers import (
    normalizar_codigo,
    normalizar_texto,
    somente_numeros,
)


def validar_nome_produto(nome):
    nome = normalizar_texto(nome)

    if not nome:
        raise ValidationError({
            'nome': 'Informe o nome do produto.'
        })

    return nome


def validar_codigo_interno(
    *,
    matriz,
    codigo_interno,
    produto_excluido=None,
):
    codigo_interno = normalizar_codigo(
        codigo_interno
    )

    if not codigo_interno:
        raise ValidationError({
            'codigo_interno': (
                'Informe o código interno do produto.'
            )
        })

    produtos = Produto.objects.filter(
        matriz=matriz,
        codigo_interno__iexact=codigo_interno,
    )

    if produto_excluido is not None:
        produtos = produtos.exclude(
            id=produto_excluido.id
        )

    if produtos.exists():
        raise ValidationError({
            'codigo_interno': (
                'Já existe um produto com este código interno.'
            )
        })

    return codigo_interno


def validar_sku(
    *,
    matriz,
    sku,
    produto_excluido=None,
):
    sku = normalizar_codigo(sku)

    if not sku:
        return ''

    produtos = Produto.objects.filter(
        matriz=matriz,
        sku__iexact=sku,
    )

    if produto_excluido is not None:
        produtos = produtos.exclude(
            id=produto_excluido.id
        )

    if produtos.exists():
        raise ValidationError({
            'sku': 'Já existe um produto com este SKU.'
        })

    return sku


def validar_gtin(
    *,
    matriz,
    gtin,
    produto_excluido=None,
):
    gtin = somente_numeros(gtin)

    if not gtin:
        return ''

    tamanhos_validos = {
        8,
        12,
        13,
        14,
    }

    if len(gtin) not in tamanhos_validos:
        raise ValidationError({
            'gtin': (
                'O GTIN deve conter 8, 12, 13 ou 14 números.'
            )
        })

    produtos = Produto.objects.filter(
        matriz=matriz,
        gtin=gtin,
    )

    if produto_excluido is not None:
        produtos = produtos.exclude(
            id=produto_excluido.id
        )

    if produtos.exists():
        raise ValidationError({
            'gtin': 'Já existe um produto com este GTIN.'
        })

    return gtin


def validar_ncm(ncm):
    ncm = somente_numeros(ncm)

    if not ncm:
        return ''

    if len(ncm) != 8:
        raise ValidationError({
            'ncm': 'O NCM deve conter exatamente 8 números.'
        })

    return ncm


def validar_decimal_nao_negativo(
    *,
    campo,
    valor,
    casas='0.00',
):
    try:
        valor_decimal = Decimal(
            str(valor if valor is not None else casas)
        )
    except (InvalidOperation, TypeError, ValueError):
        raise ValidationError({
            campo: 'Informe um valor numérico válido.'
        })

    if valor_decimal < 0:
        raise ValidationError({
            campo: 'O valor não pode ser negativo.'
        })

    return valor_decimal


def validar_inteiro_nao_negativo(
    *,
    campo,
    valor,
    permitir_nulo=True,
):
    if valor in (None, ''):
        if permitir_nulo:
            return None

        return 0

    try:
        valor_inteiro = int(valor)
    except (TypeError, ValueError):
        raise ValidationError({
            campo: 'Informe um número inteiro válido.'
        })

    if valor_inteiro < 0:
        raise ValidationError({
            campo: 'O valor não pode ser negativo.'
        })

    return valor_inteiro


def validar_dimensao(
    *,
    campo,
    valor,
):
    if valor in (None, ''):
        return None

    try:
        dimensao = Decimal(str(valor))
    except (InvalidOperation, TypeError, ValueError):
        raise ValidationError({
            campo: 'Informe uma dimensão válida.'
        })

    if dimensao <= 0:
        raise ValidationError({
            campo: 'A dimensão deve ser maior que zero.'
        })

    return dimensao


def validar_categoria(
    *,
    matriz,
    categoria,
):
    if categoria is None:
        return None

    if not isinstance(categoria, Categoria):
        raise ValidationError({
            'categoria': 'Categoria inválida.'
        })

    if categoria.matriz_id != matriz.id:
        raise ValidationError({
            'categoria': (
                'A categoria deve pertencer à mesma matriz '
                'do produto.'
            )
        })

    if not categoria.ativa:
        raise ValidationError({
            'categoria': 'A categoria selecionada está inativa.'
        })

    return categoria


def validar_marca(
    *,
    matriz,
    marca,
):
    if marca is None:
        return None

    if not isinstance(marca, Marca):
        raise ValidationError({
            'marca': 'Marca inválida.'
        })

    if marca.matriz_id != matriz.id:
        raise ValidationError({
            'marca': (
                'A marca deve pertencer à mesma matriz do produto.'
            )
        })

    if not marca.ativa:
        raise ValidationError({
            'marca': 'A marca selecionada está inativa.'
        })

    return marca


def validar_unidade_medida(
    *,
    matriz,
    unidade_medida,
):
    if not isinstance(unidade_medida, UnidadeMedida):
        raise ValidationError({
            'unidade_medida': (
                'Informe uma unidade de medida válida.'
            )
        })

    if unidade_medida.matriz_id != matriz.id:
        raise ValidationError({
            'unidade_medida': (
                'A unidade de medida deve pertencer à mesma '
                'matriz do produto.'
            )
        })

    if not unidade_medida.ativa:
        raise ValidationError({
            'unidade_medida': (
                'A unidade de medida selecionada está inativa.'
            )
        })

    return unidade_medida


def validar_pesos(
    *,
    peso_liquido_gramas,
    peso_bruto_gramas,
):
    peso_liquido = validar_inteiro_nao_negativo(
        campo='peso_liquido_gramas',
        valor=peso_liquido_gramas,
    )

    peso_bruto = validar_inteiro_nao_negativo(
        campo='peso_bruto_gramas',
        valor=peso_bruto_gramas,
    )

    if (
        peso_liquido is not None
        and peso_bruto is not None
        and peso_bruto < peso_liquido
    ):
        raise ValidationError({
            'peso_bruto_gramas': (
                'O peso bruto não pode ser menor que o peso líquido.'
            )
        })

    return peso_liquido, peso_bruto


def preparar_dados_produto(
    *,
    matriz,
    dados,
    produto_excluido=None,
):
    codigo_interno = validar_codigo_interno(
        matriz=matriz,
        codigo_interno=dados.get('codigo_interno'),
        produto_excluido=produto_excluido,
    )

    sku = validar_sku(
        matriz=matriz,
        sku=dados.get('sku'),
        produto_excluido=produto_excluido,
    )

    gtin = validar_gtin(
        matriz=matriz,
        gtin=dados.get('gtin'),
        produto_excluido=produto_excluido,
    )

    peso_liquido, peso_bruto = validar_pesos(
        peso_liquido_gramas=dados.get(
            'peso_liquido_gramas'
        ),
        peso_bruto_gramas=dados.get(
            'peso_bruto_gramas'
        ),
    )

    return {
        'categoria': validar_categoria(
            matriz=matriz,
            categoria=dados.get('categoria'),
        ),
        'marca': validar_marca(
            matriz=matriz,
            marca=dados.get('marca'),
        ),
        'unidade_medida': validar_unidade_medida(
            matriz=matriz,
            unidade_medida=dados.get('unidade_medida'),
        ),
        'codigo_interno': codigo_interno,
        'sku': sku,
        'gtin': gtin,
        'ncm': validar_ncm(
            dados.get('ncm')
        ),
        'nome': validar_nome_produto(
            dados.get('nome')
        ),
        'descricao': normalizar_texto(
            dados.get('descricao')
        ),
        'custo_base': validar_decimal_nao_negativo(
            campo='custo_base',
            valor=dados.get('custo_base'),
        ),
        'preco_venda': validar_decimal_nao_negativo(
            campo='preco_venda',
            valor=dados.get('preco_venda'),
        ),
        'origem_preco': dados.get(
            'origem_preco',
            produto_excluido.origem_preco
            if produto_excluido
            else 'manual',
        ),
        'peso_liquido_gramas': peso_liquido,
        'peso_bruto_gramas': peso_bruto,
        'altura_cm': validar_dimensao(
            campo='altura_cm',
            valor=dados.get('altura_cm'),
        ),
        'largura_cm': validar_dimensao(
            campo='largura_cm',
            valor=dados.get('largura_cm'),
        ),
        'comprimento_cm': validar_dimensao(
            campo='comprimento_cm',
            valor=dados.get('comprimento_cm'),
        ),
        'controla_estoque': dados.get(
            'controla_estoque',
            True,
        ),
        'estoque_minimo': validar_decimal_nao_negativo(
            campo='estoque_minimo',
            valor=dados.get('estoque_minimo'),
            casas='0.000',
        ),
        'status': dados.get(
            'status',
            produto_excluido.status
            if produto_excluido
            else 'ativo',
        ),
    }
