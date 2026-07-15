from django.core.exceptions import ValidationError

from core.importacao import (
    ImportadorBase,
    limpar_texto,
    normalizar_coluna,
)
from produtos.choices import (
    OrigemPreco,
    StatusProduto,
)
from produtos.models import (
    Categoria,
    Marca,
    Produto,
    UnidadeMedida,
)
from produtos.services.produtos.validacoes import (
    preparar_dados_produto,
)

from .validadores import (
    extrair_erros_validacao,
    interpretar_booleano,
    interpretar_decimal,
    interpretar_inteiro,
    normalizar_chave,
    normalizar_codigo,
    normalizar_identificador_numerico,
    serializar_decimal,
)


class ImportadorProdutos(ImportadorBase):
    colunas_esperadas = {
        'codigointerno': 'Código Interno',
        'nome': 'Nome',
        'sku': 'SKU',
        'gtin': 'GTIN',
        'ncm': 'NCM',
        'categoria': 'Categoria',
        'marca': 'Marca',
        'unidade': 'Unidade',
        'custobase': 'Custo Base',
        'precovenda': 'Preço Venda',
        'origempreco': 'Origem Preço',
        'pesoliquidogramas': 'Peso Líquido Gramas',
        'pesobrutogramas': 'Peso Bruto Gramas',
        'alturacm': 'Altura CM',
        'larguracm': 'Largura CM',
        'comprimentocm': 'Comprimento CM',
        'controlaestoque': 'Controla Estoque',
        'estoqueminimo': 'Estoque Mínimo',
        'status': 'Status',
        'descricao': 'Descrição',
    }

    def __init__(
        self,
        *,
        arquivo,
        matriz,
    ):
        super().__init__(
            arquivo=arquivo
        )

        self.matriz = matriz

        self.produtos_por_codigo = {
            produto.codigo_interno.upper(): produto
            for produto in Produto.objects.filter(
                matriz=matriz
            ).select_related(
                'categoria',
                'marca',
                'unidade_medida',
            )
        }

        categorias = Categoria.objects.filter(
            matriz=matriz,
            ativa=True,
        )

        self.categorias_por_nome = {
            normalizar_chave(categoria.nome): categoria
            for categoria in categorias
        }

        marcas = Marca.objects.filter(
            matriz=matriz,
            ativa=True,
        )

        self.marcas_por_nome = {
            normalizar_chave(marca.nome): marca
            for marca in marcas
        }

        unidades = UnidadeMedida.objects.filter(
            matriz=matriz,
            ativa=True,
        )

        self.unidades_por_chave = {}

        for unidade in unidades:
            self.unidades_por_chave[
                normalizar_chave(unidade.sigla)
            ] = unidade

            self.unidades_por_chave[
                normalizar_chave(unidade.descricao)
            ] = unidade

        self.status_por_chave = {}

        for valor, nome in StatusProduto.choices:
            self.status_por_chave[
                normalizar_chave(valor)
            ] = valor

            self.status_por_chave[
                normalizar_chave(nome)
            ] = valor

        self.origens_por_chave = {}

        for valor, nome in OrigemPreco.choices:
            self.origens_por_chave[
                normalizar_chave(valor)
            ] = valor

            self.origens_por_chave[
                normalizar_chave(nome)
            ] = valor

        self.codigos_planilha = set()
        self.skus_planilha = set()
        self.gtins_planilha = set()

    def _valor(
        self,
        *,
        linha_planilha,
        mapa_colunas,
        chave,
    ):
        coluna = mapa_colunas[
            normalizar_coluna(chave)
        ]

        return linha_planilha.get(
            coluna
        )

    def _resolver_categoria(
        self,
        valor,
    ):
        texto = limpar_texto(
            valor
        )

        if not texto:
            return None, []

        categoria = self.categorias_por_nome.get(
            normalizar_chave(texto)
        )

        if categoria is None:
            return None, [
                f'Categoria não encontrada ou inativa: {texto}.'
            ]

        return categoria, []

    def _resolver_marca(
        self,
        valor,
    ):
        texto = limpar_texto(
            valor
        )

        if not texto:
            return None, []

        marca = self.marcas_por_nome.get(
            normalizar_chave(texto)
        )

        if marca is None:
            return None, [
                f'Marca não encontrada ou inativa: {texto}.'
            ]

        return marca, []

    def _resolver_unidade(
        self,
        valor,
    ):
        texto = limpar_texto(
            valor
        )

        if not texto:
            return None, [
                'Unidade é obrigatória.'
            ]

        unidade = self.unidades_por_chave.get(
            normalizar_chave(texto)
        )

        if unidade is None:
            return None, [
                f'Unidade não encontrada ou inativa: {texto}.'
            ]

        return unidade, []

    def _resolver_status(
        self,
        valor,
        *,
        produto_existente,
    ):
        texto = limpar_texto(
            valor
        )

        if not texto:
            return (
                produto_existente.status
                if produto_existente
                else StatusProduto.ATIVO
            ), []

        status = self.status_por_chave.get(
            normalizar_chave(texto)
        )

        if status is None:
            return StatusProduto.ATIVO, [
                f'Status inválido: {texto}.'
            ]

        return status, []

    def _resolver_origem_preco(
        self,
        valor,
        *,
        produto_existente,
    ):
        texto = limpar_texto(
            valor
        )

        if not texto:
            return (
                produto_existente.origem_preco
                if produto_existente
                else OrigemPreco.MANUAL
            ), []

        origem = self.origens_por_chave.get(
            normalizar_chave(texto)
        )

        if origem is None:
            return OrigemPreco.MANUAL, [
                f'Origem de preço inválida: {texto}.'
            ]

        return origem, []

    def _validar_duplicidade_planilha(
        self,
        *,
        codigo_interno,
        sku,
        gtin,
    ):
        erros = []

        if codigo_interno in self.codigos_planilha:
            erros.append(
                (
                    'Código interno duplicado na própria '
                    'planilha.'
                )
            )
        else:
            self.codigos_planilha.add(
                codigo_interno
            )

        if sku:
            if sku in self.skus_planilha:
                erros.append(
                    'SKU duplicado na própria planilha.'
                )
            else:
                self.skus_planilha.add(
                    sku
                )

        if gtin:
            if gtin in self.gtins_planilha:
                erros.append(
                    'GTIN duplicado na própria planilha.'
                )
            else:
                self.gtins_planilha.add(
                    gtin
                )

        return erros

    def validar_linha(
        self,
        *,
        numero_linha,
        linha_planilha,
        mapa_colunas,
    ):
        codigo_interno = normalizar_codigo(
            self._valor(
                linha_planilha=linha_planilha,
                mapa_colunas=mapa_colunas,
                chave='codigointerno',
            )
        )

        produto_existente = (
            self.produtos_por_codigo.get(
                codigo_interno
            )
            if codigo_interno
            else None
        )

        nome = limpar_texto(
            self._valor(
                linha_planilha=linha_planilha,
                mapa_colunas=mapa_colunas,
                chave='nome',
            )
        )

        sku = normalizar_codigo(
            self._valor(
                linha_planilha=linha_planilha,
                mapa_colunas=mapa_colunas,
                chave='sku',
            )
        )

        gtin = normalizar_identificador_numerico(
            self._valor(
                linha_planilha=linha_planilha,
                mapa_colunas=mapa_colunas,
                chave='gtin',
            )
        )

        ncm = normalizar_identificador_numerico(
            self._valor(
                linha_planilha=linha_planilha,
                mapa_colunas=mapa_colunas,
                chave='ncm',
            )
        )

        descricao = limpar_texto(
            self._valor(
                linha_planilha=linha_planilha,
                mapa_colunas=mapa_colunas,
                chave='descricao',
            )
        )

        erros = []

        if not codigo_interno:
            erros.append(
                'Código interno é obrigatório.'
            )

        erros.extend(
            self._validar_duplicidade_planilha(
                codigo_interno=codigo_interno,
                sku=sku,
                gtin=gtin,
            )
            if codigo_interno
            else []
        )

        categoria, erros_categoria = (
            self._resolver_categoria(
                self._valor(
                    linha_planilha=linha_planilha,
                    mapa_colunas=mapa_colunas,
                    chave='categoria',
                )
            )
        )
        erros.extend(
            erros_categoria
        )

        marca, erros_marca = self._resolver_marca(
            self._valor(
                linha_planilha=linha_planilha,
                mapa_colunas=mapa_colunas,
                chave='marca',
            )
        )
        erros.extend(
            erros_marca
        )

        unidade, erros_unidade = (
            self._resolver_unidade(
                self._valor(
                    linha_planilha=linha_planilha,
                    mapa_colunas=mapa_colunas,
                    chave='unidade',
                )
            )
        )
        erros.extend(
            erros_unidade
        )

        custo_base, erros_custo = interpretar_decimal(
            self._valor(
                linha_planilha=linha_planilha,
                mapa_colunas=mapa_colunas,
                chave='custobase',
            ),
            campo='Custo base',
            obrigatorio=True,
            padrao=0,
        )
        erros.extend(
            erros_custo
        )

        preco_venda, erros_preco = interpretar_decimal(
            self._valor(
                linha_planilha=linha_planilha,
                mapa_colunas=mapa_colunas,
                chave='precovenda',
            ),
            campo='Preço de venda',
            obrigatorio=True,
            padrao=0,
        )
        erros.extend(
            erros_preco
        )

        estoque_minimo, erros_estoque = interpretar_decimal(
            self._valor(
                linha_planilha=linha_planilha,
                mapa_colunas=mapa_colunas,
                chave='estoqueminimo',
            ),
            campo='Estoque mínimo',
            padrao=0,
        )
        erros.extend(
            erros_estoque
        )

        peso_liquido, erros_peso_liquido = interpretar_inteiro(
            self._valor(
                linha_planilha=linha_planilha,
                mapa_colunas=mapa_colunas,
                chave='pesoliquidogramas',
            ),
            campo='Peso líquido',
        )
        erros.extend(
            erros_peso_liquido
        )

        peso_bruto, erros_peso_bruto = interpretar_inteiro(
            self._valor(
                linha_planilha=linha_planilha,
                mapa_colunas=mapa_colunas,
                chave='pesobrutogramas',
            ),
            campo='Peso bruto',
        )
        erros.extend(
            erros_peso_bruto
        )

        altura, erros_altura = interpretar_decimal(
            self._valor(
                linha_planilha=linha_planilha,
                mapa_colunas=mapa_colunas,
                chave='alturacm',
            ),
            campo='Altura',
        )
        erros.extend(
            erros_altura
        )

        largura, erros_largura = interpretar_decimal(
            self._valor(
                linha_planilha=linha_planilha,
                mapa_colunas=mapa_colunas,
                chave='larguracm',
            ),
            campo='Largura',
        )
        erros.extend(
            erros_largura
        )

        comprimento, erros_comprimento = interpretar_decimal(
            self._valor(
                linha_planilha=linha_planilha,
                mapa_colunas=mapa_colunas,
                chave='comprimentocm',
            ),
            campo='Comprimento',
        )
        erros.extend(
            erros_comprimento
        )

        controla_estoque, erros_controle = interpretar_booleano(
            self._valor(
                linha_planilha=linha_planilha,
                mapa_colunas=mapa_colunas,
                chave='controlaestoque',
            ),
            campo='Controla estoque',
            padrao=True,
        )
        erros.extend(
            erros_controle
        )

        status, erros_status = self._resolver_status(
            self._valor(
                linha_planilha=linha_planilha,
                mapa_colunas=mapa_colunas,
                chave='status',
            ),
            produto_existente=produto_existente,
        )
        erros.extend(
            erros_status
        )

        origem_preco, erros_origem = (
            self._resolver_origem_preco(
                self._valor(
                    linha_planilha=linha_planilha,
                    mapa_colunas=mapa_colunas,
                    chave='origempreco',
                ),
                produto_existente=produto_existente,
            )
        )
        erros.extend(
            erros_origem
        )

        dados = {
            'categoria': categoria,
            'marca': marca,
            'unidade_medida': unidade,
            'codigo_interno': codigo_interno,
            'sku': sku,
            'gtin': gtin,
            'ncm': ncm,
            'nome': nome,
            'descricao': descricao,
            'custo_base': custo_base,
            'preco_venda': preco_venda,
            'origem_preco': origem_preco,
            'peso_liquido_gramas': peso_liquido,
            'peso_bruto_gramas': peso_bruto,
            'altura_cm': altura,
            'largura_cm': largura,
            'comprimento_cm': comprimento,
            'controla_estoque': controla_estoque,
            'estoque_minimo': estoque_minimo,
            'status': status,
        }

        if not erros:
            try:
                dados = preparar_dados_produto(
                    matriz=self.matriz,
                    dados=dados,
                    produto_excluido=produto_existente,
                )
            except ValidationError as erro:
                erros.extend(
                    extrair_erros_validacao(
                        erro
                    )
                )

        acao_prevista = (
            'atualizar'
            if produto_existente
            else 'novo'
        )

        valido = not erros

        return {
            'linha': numero_linha,
            'produto_id': (
                produto_existente.id
                if produto_existente
                else None
            ),
            'codigo_interno': codigo_interno,
            'nome': nome,
            'sku': sku,
            'gtin': gtin,
            'ncm': ncm,
            'descricao': descricao,
            'categoria_id': (
                categoria.id
                if categoria
                else None
            ),
            'categoria_nome': (
                categoria.nome
                if categoria
                else ''
            ),
            'marca_id': (
                marca.id
                if marca
                else None
            ),
            'marca_nome': (
                marca.nome
                if marca
                else ''
            ),
            'unidade_medida_id': (
                unidade.id
                if unidade
                else None
            ),
            'unidade_medida_nome': (
                str(unidade)
                if unidade
                else ''
            ),
            'custo_base': serializar_decimal(
                custo_base
            ),
            'preco_venda': serializar_decimal(
                preco_venda
            ),
            'origem_preco': origem_preco,
            'peso_liquido_gramas': peso_liquido,
            'peso_bruto_gramas': peso_bruto,
            'altura_cm': serializar_decimal(
                altura
            ),
            'largura_cm': serializar_decimal(
                largura
            ),
            'comprimento_cm': serializar_decimal(
                comprimento
            ),
            'controla_estoque': controla_estoque,
            'estoque_minimo': serializar_decimal(
                estoque_minimo
            ),
            'produto_status': status,
            'acao_prevista': acao_prevista,
            'status': (
                acao_prevista
                if valido
                else 'invalido'
            ),
            'valido': valido,
            'erros': erros,
        }


def validar_planilha_produtos(
    *,
    arquivo,
    matriz,
):
    resultado = ImportadorProdutos(
        arquivo=arquivo,
        matriz=matriz,
    ).processar()

    dados = resultado.como_dict()

    resumo = dados.get(
        'resumo'
    ) or {}

    resumo['novos'] = resumo.get(
        'novo',
        0
    )

    resumo['atualizar'] = resumo.get(
        'atualizar',
        0
    )

    dados['resumo'] = resumo

    return dados
