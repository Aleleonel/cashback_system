from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError
from django.test import TestCase

from core.choices import StatusOperacional
from empresas.models import Loja, Matriz
from estoque.models import SaldoEstoque
from produtos.models import Produto, UnidadeMedida


class SaldoEstoqueModelTestCase(TestCase):
    def setUp(self):
        self.matriz = Matriz.objects.create(
            nome='Matriz Estoque'
        )

        self.loja = Loja.objects.create(
            matriz=self.matriz,
            nome='Loja Estoque',
            status=StatusOperacional.ATIVA,
        )

        self.unidade = UnidadeMedida.objects.create(
            matriz=self.matriz,
            sigla='UN',
            descricao='Unidade',
        )

        self.produto = Produto.objects.create(
            matriz=self.matriz,
            unidade_medida=self.unidade,
            codigo_interno='EST-001',
            nome='Produto Estoque',
            controla_estoque=True,
        )

    def criar_saldo(self, **dados):
        padrao = {
            'matriz': self.matriz,
            'loja': self.loja,
            'produto': self.produto,
            'quantidade_atual': Decimal('0.000'),
        }

        padrao.update(dados)

        return SaldoEstoque.objects.create(**padrao)

    def test_cria_saldo_zerado_valido(self):
        saldo = self.criar_saldo()

        self.assertEqual(
            saldo.quantidade_atual,
            Decimal('0.000')
        )
        self.assertIsNone(saldo.ultima_movimentacao_em)
        self.assertIsNotNone(saldo.uuid)
        self.assertIsNotNone(saldo.criado_em)
        self.assertIsNotNone(saldo.atualizado_em)

    def test_aceita_quantidade_com_tres_casas_decimais(self):
        saldo = self.criar_saldo(
            quantidade_atual=Decimal('10.125')
        )

        saldo.refresh_from_db()

        self.assertEqual(
            saldo.quantidade_atual,
            Decimal('10.125')
        )

    def test_rejeita_quantidade_negativa_no_model(self):
        saldo = SaldoEstoque(
            matriz=self.matriz,
            loja=self.loja,
            produto=self.produto,
            quantidade_atual=Decimal('-0.001'),
        )

        with self.assertRaises(ValidationError):
            saldo.full_clean()

    def test_rejeita_quantidade_negativa_no_banco(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                SaldoEstoque.objects.bulk_create([
                    SaldoEstoque(
                        matriz=self.matriz,
                        loja=self.loja,
                        produto=self.produto,
                        quantidade_atual=Decimal('-1.000'),
                    )
                ])

    def test_impede_saldo_duplicado(self):
        self.criar_saldo()

        with self.assertRaises(ValidationError):
            self.criar_saldo()

    def test_constraint_impede_saldo_duplicado_no_banco(self):
        self.criar_saldo()

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                SaldoEstoque.objects.bulk_create([
                    SaldoEstoque(
                        matriz=self.matriz,
                        loja=self.loja,
                        produto=self.produto,
                        quantidade_atual=Decimal('0.000'),
                    )
                ])

    def test_rejeita_loja_de_outra_matriz(self):
        outra_matriz = Matriz.objects.create(
            nome='Outra Matriz'
        )

        outra_loja = Loja.objects.create(
            matriz=outra_matriz,
            nome='Outra Loja',
            status=StatusOperacional.ATIVA,
        )

        saldo = SaldoEstoque(
            matriz=self.matriz,
            loja=outra_loja,
            produto=self.produto,
        )

        with self.assertRaises(ValidationError) as contexto:
            saldo.full_clean()

        self.assertIn(
            'loja',
            contexto.exception.message_dict
        )

    def test_rejeita_produto_de_outra_matriz(self):
        outra_matriz = Matriz.objects.create(
            nome='Outra Matriz Produto'
        )

        outra_unidade = UnidadeMedida.objects.create(
            matriz=outra_matriz,
            sigla='CX',
            descricao='Caixa',
        )

        outro_produto = Produto.objects.create(
            matriz=outra_matriz,
            unidade_medida=outra_unidade,
            codigo_interno='OUT-001',
            nome='Outro Produto',
        )

        saldo = SaldoEstoque(
            matriz=self.matriz,
            loja=self.loja,
            produto=outro_produto,
        )

        with self.assertRaises(ValidationError) as contexto:
            saldo.full_clean()

        self.assertIn(
            'produto',
            contexto.exception.message_dict
        )

    def test_rejeita_produto_que_nao_controla_estoque(self):
        produto_sem_estoque = Produto.objects.create(
            matriz=self.matriz,
            unidade_medida=self.unidade,
            codigo_interno='SEM-EST-001',
            nome='Produto sem controle de estoque',
            controla_estoque=False,
        )

        saldo = SaldoEstoque(
            matriz=self.matriz,
            loja=self.loja,
            produto=produto_sem_estoque,
        )

        with self.assertRaises(ValidationError) as contexto:
            saldo.full_clean()

        self.assertIn(
            'produto',
            contexto.exception.message_dict
        )

        self.assertIn(
            'não controla estoque',
            contexto.exception.message_dict['produto'][0]
        )

    def test_save_rejeita_produto_que_nao_controla_estoque(self):
        produto_sem_estoque = Produto.objects.create(
            matriz=self.matriz,
            unidade_medida=self.unidade,
            codigo_interno='SEM-EST-002',
            nome='Outro produto sem controle de estoque',
            controla_estoque=False,
        )

        with self.assertRaises(ValidationError):
            SaldoEstoque.objects.create(
                matriz=self.matriz,
                loja=self.loja,
                produto=produto_sem_estoque,
            )

    def test_relacao_com_matriz_e_protegida(self):
        saldo = self.criar_saldo()

        with self.assertRaises(ProtectedError):
            saldo.matriz.delete()

    def test_relacao_com_loja_e_protegida(self):
        saldo = self.criar_saldo()

        with self.assertRaises(ProtectedError):
            saldo.loja.delete()

    def test_relacao_com_produto_e_protegida(self):
        saldo = self.criar_saldo()

        with self.assertRaises(ProtectedError):
            saldo.produto.delete()

    def test_string_do_saldo(self):
        saldo = self.criar_saldo(
            quantidade_atual=Decimal('7.500')
        )

        self.assertEqual(
            str(saldo),
            'Loja Estoque - EST-001 - 7.500'
        )

