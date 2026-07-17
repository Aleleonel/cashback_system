from django.test import TestCase

from empresas.models import Matriz

from compras.choices import StatusFornecedor
from compras.models import Fornecedor
from compras.selectors import (
    get_fornecedor_por_cnpj,
    get_fornecedores,
)


class FornecedorSelectorsTestCase(TestCase):
    def setUp(self):
        self.matriz = Matriz.objects.create(
            nome='Matriz Selectors'
        )

        self.outra_matriz = Matriz.objects.create(
            nome='Outra Matriz'
        )

        self.fornecedor = Fornecedor.objects.create(
            matriz=self.matriz,
            razao_social='Fornecedor Ativo LTDA',
            nome_fantasia='Ativo Brasil',
            cnpj='11222333000181',
            status=StatusFornecedor.ATIVO,
        )

        Fornecedor.objects.create(
            matriz=self.outra_matriz,
            razao_social='Fornecedor Externo LTDA',
            cnpj='11444777000161',
        )

    def test_lista_apenas_fornecedores_da_matriz(self):
        resultado = get_fornecedores(
            matriz=self.matriz
        )

        self.assertEqual(
            list(resultado),
            [self.fornecedor],
        )

    def test_busca_por_cnpj_normaliza_documento(self):
        resultado = get_fornecedor_por_cnpj(
            matriz=self.matriz,
            cnpj='11.222.333/0001-81',
        )

        self.assertEqual(
            resultado,
            self.fornecedor,
        )