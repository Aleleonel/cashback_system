from datetime import date
from decimal import Decimal
from io import BytesIO

import pandas as pd
from django.test import SimpleTestCase
from openpyxl import load_workbook

from core.importacao import (
    CONTENT_TYPE_XLSX,
    ImportadorBase,
    ResultadoImportacao,
    converter_booleano,
    converter_data,
    converter_decimal,
    criar_resposta_download_excel,
    gerar_modelo_excel,
    limpar_numero,
    limpar_texto,
    normalizar_coluna,
    serializar_data_sessao,
)


class ImportadorExemplo(ImportadorBase):
    colunas_esperadas = {
        'codigo': 'Código',
        'nome': 'Nome',
    }

    def validar_linha(
        self,
        *,
        numero_linha,
        linha_planilha,
        mapa_colunas,
    ):
        codigo = limpar_texto(
            linha_planilha.get(
                mapa_colunas['codigo']
            )
        )

        nome = limpar_texto(
            linha_planilha.get(
                mapa_colunas['nome']
            )
        )

        erros = []

        if not codigo:
            erros.append(
                'Código obrigatório.'
            )

        if not nome:
            erros.append(
                'Nome obrigatório.'
            )

        return {
            'linha': numero_linha,
            'codigo': codigo,
            'nome': nome,
            'status': 'novo',
            'valido': not erros,
            'erros': erros,
        }


def criar_excel_teste(
    *,
    colunas,
    linhas,
):
    dataframe = pd.DataFrame(
        linhas,
        columns=colunas,
    )

    arquivo = BytesIO()

    dataframe.to_excel(
        arquivo,
        index=False,
    )

    arquivo.seek(0)

    return arquivo


class ResultadoImportacaoTestCase(SimpleTestCase):
    def test_resultado_calcula_possui_validos(self):
        resultado = ResultadoImportacao(
            resumo={
                'total': 2,
                'validos': 1,
                'invalidos': 1,
            }
        )

        self.assertTrue(
            resultado.possui_validos
        )

    def test_resultado_compativel_com_formato_legado(self):
        resultado = ResultadoImportacao(
            estrutura_ok=True,
            linhas=[{
                'linha': 2,
                'valido': True,
            }],
            resumo={
                'total': 1,
                'validos': 1,
                'invalidos': 0,
            },
        )

        dados = resultado.como_dict()

        self.assertTrue(
            dados['valido']
        )
        self.assertEqual(
            dados['linhas'][0]['linha'],
            2
        )
        self.assertTrue(
            dados['possui_validos']
        )

    def test_falha_estrutura_padronizada(self):
        resultado = ResultadoImportacao.falha_estrutura(
            'Coluna ausente.'
        )

        self.assertFalse(
            resultado.estrutura_ok
        )
        self.assertEqual(
            resultado.erro_estrutura,
            'Coluna ausente.'
        )


class ValidacoesImportacaoTestCase(SimpleTestCase):
    def test_normaliza_coluna_com_acentos_e_separadores(self):
        self.assertEqual(
            normalizar_coluna(
                'Código Interno'
            ),
            'codigointerno'
        )

        self.assertEqual(
            normalizar_coluna(
                'E-mail'
            ),
            'email'
        )

    def test_limpa_texto_e_numero(self):
        self.assertEqual(
            limpar_texto(' Produto '),
            'Produto'
        )
        self.assertEqual(
            limpar_numero(
                '789.123.456-00'
            ),
            '78912345600'
        )

    def test_converte_data(self):
        self.assertEqual(
            converter_data(
                '31/12/2026'
            ),
            date(2026, 12, 31)
        )

        self.assertEqual(
            serializar_data_sessao(
                date(2026, 12, 31)
            ),
            '2026-12-31'
        )

    def test_converte_decimal_brasileiro(self):
        self.assertEqual(
            converter_decimal(
                'R$ 1.234,56'
            ),
            Decimal('1234.56')
        )

    def test_converte_booleanos(self):
        self.assertTrue(
            converter_booleano('Sim')
        )
        self.assertFalse(
            converter_booleano('Não')
        )


class ExcelImportacaoTestCase(SimpleTestCase):
    def test_gera_modelo_excel_valido(self):
        arquivo = gerar_modelo_excel(
            nome_aba='Produtos',
            colunas=[
                'Código',
                'Nome',
            ],
            linhas_exemplo=[
                [
                    'PROD-001',
                    'Produto exemplo',
                ]
            ],
        )

        workbook = load_workbook(
            arquivo
        )

        worksheet = workbook['Produtos']

        self.assertEqual(
            worksheet['A1'].value,
            'Código'
        )
        self.assertEqual(
            worksheet['B2'].value,
            'Produto exemplo'
        )
        self.assertEqual(
            worksheet.freeze_panes,
            'A2'
        )

    def test_cria_resposta_download_excel(self):
        arquivo = gerar_modelo_excel(
            nome_aba='Produtos',
            colunas=['Código'],
        )

        response = criar_resposta_download_excel(
            arquivo=arquivo,
            nome_arquivo='modelo_produtos.xlsx',
        )

        self.assertEqual(
            response.status_code,
            200
        )
        self.assertEqual(
            response['Content-Type'],
            CONTENT_TYPE_XLSX
        )
        self.assertIn(
            'modelo_produtos.xlsx',
            response['Content-Disposition']
        )


class ImportadorBaseTestCase(SimpleTestCase):
    def test_processa_planilha_valida(self):
        arquivo = criar_excel_teste(
            colunas=[
                'Código',
                'Nome',
            ],
            linhas=[
                [
                    'PROD-001',
                    'Produto exemplo',
                ],
                [
                    '',
                    'Produto sem código',
                ],
            ],
        )

        resultado = ImportadorExemplo(
            arquivo=arquivo
        ).processar()

        self.assertTrue(
            resultado.estrutura_ok
        )
        self.assertEqual(
            resultado.resumo['total'],
            2
        )
        self.assertEqual(
            resultado.resumo['validos'],
            1
        )
        self.assertEqual(
            resultado.resumo['invalidos'],
            1
        )

    def test_detecta_colunas_obrigatorias_ausentes(self):
        arquivo = criar_excel_teste(
            colunas=['Código'],
            linhas=[
                ['PROD-001']
            ],
        )

        resultado = ImportadorExemplo(
            arquivo=arquivo
        ).processar()

        self.assertFalse(
            resultado.estrutura_ok
        )
        self.assertIn(
            'Nome',
            resultado.erro_estrutura
        )

    def test_erro_de_leitura_retorna_falha_controlada(self):
        arquivo = BytesIO(
            b'conteudo-invalido'
        )

        resultado = ImportadorExemplo(
            arquivo=arquivo
        ).processar()

        self.assertFalse(
            resultado.estrutura_ok
        )
        self.assertIn(
            'Não foi possível ler',
            resultado.erro_estrutura
        )
