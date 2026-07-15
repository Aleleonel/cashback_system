from io import BytesIO

import pandas as pd
from django.test import TestCase
from openpyxl import load_workbook

from clientes.importacao import (
    criar_download_modelo_clientes,
    gerar_modelo_importacao_clientes,
    validar_planilha_clientes_compartilhada,
)
from clientes.models import Cliente
from empresas.models import Loja, Matriz


def criar_planilha_clientes(
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


class ImportacaoClientesCompartilhadaTestCase(TestCase):
    def setUp(self):
        self.matriz = Matriz.objects.create(
            nome='Matriz Importação'
        )

        self.loja = Loja.objects.create(
            matriz=self.matriz,
            nome='Loja Importação'
        )

        self.loja = Loja.objects.create(
            matriz=self.matriz,
            nome='Loja Importação'
        )

    def test_valida_planilha_com_cliente_novo(self):
        arquivo = criar_planilha_clientes(
            colunas=[
                'Nome',
                'CPF',
                'Nascimento',
                'Celular',
                'E-mail',
            ],
            linhas=[
                [
                    'João Silva',
                    '123.456.789-00',
                    '01/01/1990',
                    '(11) 99999-9999',
                    'joao@email.com',
                ]
            ],
        )

        resultado = (
            validar_planilha_clientes_compartilhada(
                arquivo=arquivo,
                matriz=self.matriz,
            )
        )

        self.assertTrue(
            resultado['valido']
        )
        self.assertTrue(
            resultado['possui_validos']
        )
        self.assertEqual(
            resultado['resumo']['total'],
            1
        )
        self.assertEqual(
            resultado['resumo']['validos'],
            1
        )
        self.assertEqual(
            resultado['resumo']['invalidos'],
            0
        )
        self.assertEqual(
            resultado['resumo']['novo'],
            1
        )

        linha = resultado['linhas'][0]

        self.assertEqual(
            linha['cpf'],
            '12345678900'
        )
        self.assertEqual(
            linha['celular'],
            '11999999999'
        )
        self.assertEqual(
            linha['nascimento'],
            '1990-01-01'
        )
        self.assertEqual(
            linha['status'],
            'novo'
        )

    def test_identifica_cliente_existente_para_atualizacao(self):
        Cliente.objects.create(
            matriz=self.matriz,
            loja_cadastro=self.loja,
            nome='Cliente Existente',
            nome_normalizado='cliente existente',
            cpf='12345678900',
            cpf_normalizado='12345678900',
            ativo=True,
        )

        arquivo = criar_planilha_clientes(
            colunas=[
                'Nome',
                'CPF',
                'Nascimento',
                'Celular',
                'E-mail',
            ],
            linhas=[
                [
                    'Cliente Atualizado',
                    '12345678900',
                    '',
                    '11988887777',
                    'cliente@email.com',
                ]
            ],
        )

        resultado = (
            validar_planilha_clientes_compartilhada(
                arquivo=arquivo,
                matriz=self.matriz,
            )
        )

        self.assertEqual(
            resultado['resumo']['atualizar'],
            1
        )
        self.assertEqual(
            resultado['linhas'][0]['status'],
            'atualizar'
        )

    def test_detecta_dados_invalidos(self):
        arquivo = criar_planilha_clientes(
            colunas=[
                'Nome',
                'CPF',
                'Nascimento',
                'Celular',
                'E-mail',
            ],
            linhas=[
                [
                    'João',
                    '123',
                    'data-invalida',
                    '',
                    'email-invalido',
                ]
            ],
        )

        resultado = (
            validar_planilha_clientes_compartilhada(
                arquivo=arquivo,
                matriz=self.matriz,
            )
        )

        self.assertTrue(
            resultado['valido']
        )
        self.assertFalse(
            resultado['possui_validos']
        )
        self.assertEqual(
            resultado['resumo']['invalidos'],
            1
        )

        erros = resultado['linhas'][0]['erros']

        self.assertIn(
            'Informe nome completo.',
            erros
        )
        self.assertIn(
            'CPF deve conter 11 números.',
            erros
        )
        self.assertIn(
            'Nascimento inválido.',
            erros
        )
        self.assertIn(
            'E-mail inválido.',
            erros
        )

    def test_detecta_colunas_ausentes(self):
        arquivo = criar_planilha_clientes(
            colunas=[
                'Nome',
                'CPF',
            ],
            linhas=[
                [
                    'João Silva',
                    '12345678900',
                ]
            ],
        )

        resultado = (
            validar_planilha_clientes_compartilhada(
                arquivo=arquivo,
                matriz=self.matriz,
            )
        )

        self.assertFalse(
            resultado['valido']
        )
        self.assertIn(
            'Nascimento',
            resultado['erro_estrutura']
        )
        self.assertIn(
            'Celular',
            resultado['erro_estrutura']
        )
        self.assertIn(
            'E-mail',
            resultado['erro_estrutura']
        )

    def test_aceita_cabecalhos_com_variacoes(self):
        arquivo = criar_planilha_clientes(
            colunas=[
                ' nome ',
                'CPF',
                'NASCIMENTO',
                'celular',
                'E_mail',
            ],
            linhas=[
                [
                    'Maria Souza',
                    '98765432100',
                    '1995-05-10',
                    '11977776666',
                    'maria@email.com',
                ]
            ],
        )

        resultado = (
            validar_planilha_clientes_compartilhada(
                arquivo=arquivo,
                matriz=self.matriz,
            )
        )

        self.assertTrue(
            resultado['valido']
        )
        self.assertEqual(
            resultado['resumo']['validos'],
            1
        )

    def test_gera_modelo_excel_de_clientes(self):
        arquivo = gerar_modelo_importacao_clientes()

        workbook = load_workbook(
            arquivo
        )

        worksheet = workbook['Clientes']

        self.assertEqual(
            worksheet['A1'].value,
            'Nome'
        )
        self.assertEqual(
            worksheet['E1'].value,
            'E-mail'
        )
        self.assertEqual(
            worksheet['A2'].value,
            'João Silva'
        )

    def test_cria_download_do_modelo(self):
        response = criar_download_modelo_clientes()

        self.assertEqual(
            response.status_code,
            200
        )
        self.assertIn(
            'modelo_importacao_clientes.xlsx',
            response['Content-Disposition']
        )

