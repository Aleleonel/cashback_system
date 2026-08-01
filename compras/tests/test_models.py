from django.db import IntegrityError, transaction
from django.test import TestCase

from empresas.models import Matriz

from compras.choices import StatusFornecedor
from compras.models import Fornecedor


class FornecedorModelTestCase(TestCase):
    def setUp(self):
        self.matriz = Matriz.objects.create(
            nome='Matriz Compras'
        )

    def test_cria_fornecedor(self):
        fornecedor = Fornecedor.objects.create(
            matriz=self.matriz,
            razao_social='Fornecedor Teste LTDA',
            nome_fantasia='Fornecedor Teste',
            cnpj='11222333000181',
        )

        self.assertIsNotNone(fornecedor.uuid)
        self.assertEqual(
            fornecedor.status,
            StatusFornecedor.ATIVO,
        )

    def test_impede_cnpj_duplicado_na_mesma_matriz(self):
        Fornecedor.objects.create(
            matriz=self.matriz,
            razao_social='Fornecedor Um LTDA',
            cnpj='11222333000181',
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Fornecedor.objects.create(
                    matriz=self.matriz,
                    razao_social='Fornecedor Dois LTDA',
                    cnpj='11222333000181',
                )

    def test_permite_cnpj_vazio_em_varios_fornecedores(self):
        Fornecedor.objects.create(
            matriz=self.matriz,
            razao_social='Fornecedor Um LTDA',
            cnpj='',
        )

        Fornecedor.objects.create(
            matriz=self.matriz,
            razao_social='Fornecedor Dois LTDA',
            cnpj='',
        )

        self.assertEqual(
            Fornecedor.objects.count(),
            2,
        )