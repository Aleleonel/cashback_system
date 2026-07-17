from decimal import Decimal
from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.test import TestCase

from auditoria.models import RegistroAuditoria
from core.choices import StatusOperacional
from empresas.models import Loja, Matriz
from estoque.choices import (
    OrigemMovimentacao,
    TipoMovimentacao,
)
from estoque.models import MovimentacaoEstoque, SaldoEstoque
from estoque.services import registrar_entrada_estoque
from produtos.models import Produto, UnidadeMedida


class RegistrarEntradaEstoqueTestCase(TestCase):
    def setUp(self):
        self.matriz = Matriz.objects.create(
            nome='Matriz Service Entrada'
        )

        self.loja = Loja.objects.create(
            matriz=self.matriz,
            nome='Loja Service Entrada',
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
            codigo_interno='ENT-001',
            nome='Produto de entrada',
            controla_estoque=True,
        )

    def registrar_entrada(self, **dados):
        padrao = {
            'matriz': self.matriz,
            'loja': self.loja,
            'produto': self.produto,
            'tipo': TipoMovimentacao.ENTRADA_MANUAL,
            'origem': OrigemMovimentacao.MANUAL,
            'quantidade': Decimal('5.000'),
            'chave_idempotencia': 'entrada:teste:001',
        }

        padrao.update(dados)

        return registrar_entrada_estoque(**padrao)

    def test_primeira_entrada_cria_saldo_e_movimentacao(self):
        resultado = self.registrar_entrada()

        self.assertFalse(resultado.duplicada)

        self.assertEqual(
            resultado.saldo.quantidade_atual,
            Decimal('5.000')
        )

        self.assertEqual(
            resultado.movimentacao.saldo_anterior,
            Decimal('0.000')
        )

        self.assertEqual(
            resultado.movimentacao.saldo_posterior,
            Decimal('5.000')
        )

        self.assertEqual(
            SaldoEstoque.objects.count(),
            1
        )

        self.assertEqual(
            MovimentacaoEstoque.objects.count(),
            1
        )

    def test_entrada_posterior_acumula_saldo(self):
        self.registrar_entrada()

        resultado = self.registrar_entrada(
            quantidade=Decimal('2.500'),
            chave_idempotencia='entrada:teste:002',
        )

        self.assertEqual(
            resultado.saldo.quantidade_atual,
            Decimal('7.500')
        )

        self.assertEqual(
            resultado.movimentacao.saldo_anterior,
            Decimal('5.000')
        )

        self.assertEqual(
            resultado.movimentacao.saldo_posterior,
            Decimal('7.500')
        )

    def test_idempotencia_nao_aplica_entrada_duas_vezes(self):
        primeiro = self.registrar_entrada()
        segundo = self.registrar_entrada()

        self.assertFalse(primeiro.duplicada)
        self.assertTrue(segundo.duplicada)

        self.assertEqual(
            primeiro.movimentacao.pk,
            segundo.movimentacao.pk
        )

        saldo = SaldoEstoque.objects.get(
            matriz=self.matriz,
            loja=self.loja,
            produto=self.produto,
        )

        self.assertEqual(
            saldo.quantidade_atual,
            Decimal('5.000')
        )

        self.assertEqual(
            MovimentacaoEstoque.objects.count(),
            1
        )

    def test_mesma_chave_com_quantidade_diferente_gera_conflito(self):
        self.registrar_entrada()

        with self.assertRaises(ValidationError) as contexto:
            self.registrar_entrada(
                quantidade=Decimal('8.000')
            )

        self.assertIn(
            'chave_idempotencia',
            contexto.exception.message_dict
        )

        saldo = SaldoEstoque.objects.get(
            matriz=self.matriz,
            loja=self.loja,
            produto=self.produto,
        )

        self.assertEqual(
            saldo.quantidade_atual,
            Decimal('5.000')
        )

        self.assertEqual(
            MovimentacaoEstoque.objects.count(),
            1
        )

    def test_mesma_chave_com_produto_diferente_gera_conflito(self):
        self.registrar_entrada()

        outro_produto = Produto.objects.create(
            matriz=self.matriz,
            unidade_medida=self.unidade,
            codigo_interno='ENT-002',
            nome='Segundo produto de entrada',
            controla_estoque=True,
        )

        with self.assertRaises(ValidationError) as contexto:
            self.registrar_entrada(
                produto=outro_produto
            )

        self.assertIn(
            'chave_idempotencia',
            contexto.exception.message_dict
        )

        self.assertFalse(
            SaldoEstoque.objects.filter(
                produto=outro_produto
            ).exists()
        )

        self.assertEqual(
            MovimentacaoEstoque.objects.count(),
            1
        )

    def test_exige_chave_de_idempotencia(self):
        with self.assertRaises(ValidationError) as contexto:
            self.registrar_entrada(
                chave_idempotencia=''
            )

        self.assertIn(
            'chave_idempotencia',
            contexto.exception.message_dict
        )

    def test_rejeita_quantidade_zero(self):
        with self.assertRaises(ValidationError):
            self.registrar_entrada(
                quantidade=Decimal('0.000')
            )

    def test_rejeita_quantidade_negativa(self):
        with self.assertRaises(ValidationError):
            self.registrar_entrada(
                quantidade=Decimal('-1.000')
            )

    def test_rejeita_quantidade_invalida(self):
        with self.assertRaises(ValidationError):
            self.registrar_entrada(
                quantidade='quantidade-invalida'
            )

    def test_rejeita_quantidade_nao_finita(self):
        for quantidade in (
            'NaN',
            'Infinity',
            '-Infinity',
        ):
            with self.subTest(quantidade=quantidade):
                with self.assertRaises(ValidationError):
                    self.registrar_entrada(
                        quantidade=quantidade
                    )

    def test_normaliza_quantidade_para_tres_casas(self):
        resultado = self.registrar_entrada(
            quantidade='2.5'
        )

        self.assertEqual(
            resultado.movimentacao.quantidade,
            Decimal('2.500')
        )

    def test_rejeita_tipo_de_saida(self):
        with self.assertRaises(ValidationError) as contexto:
            self.registrar_entrada(
                tipo=TipoMovimentacao.SAIDA_MANUAL
            )

        self.assertIn(
            'tipo',
            contexto.exception.message_dict
        )

    def test_rejeita_loja_de_outra_matriz(self):
        outra_matriz = Matriz.objects.create(
            nome='Outra Matriz Service'
        )

        outra_loja = Loja.objects.create(
            matriz=outra_matriz,
            nome='Outra Loja Service',
            status=StatusOperacional.ATIVA,
        )

        with self.assertRaises(ValidationError):
            self.registrar_entrada(
                loja=outra_loja
            )

    def test_rejeita_produto_de_outra_matriz(self):
        outra_matriz = Matriz.objects.create(
            nome='Matriz Produto Service'
        )

        outra_unidade = UnidadeMedida.objects.create(
            matriz=outra_matriz,
            sigla='CX',
            descricao='Caixa',
        )

        outro_produto = Produto.objects.create(
            matriz=outra_matriz,
            unidade_medida=outra_unidade,
            codigo_interno='ENT-OUT-001',
            nome='Produto de outra matriz',
            controla_estoque=True,
        )

        with self.assertRaises(ValidationError):
            self.registrar_entrada(
                produto=outro_produto
            )

    def test_rejeita_produto_sem_controle_de_estoque(self):
        produto_sem_estoque = Produto.objects.create(
            matriz=self.matriz,
            unidade_medida=self.unidade,
            codigo_interno='ENT-SEM-001',
            nome='Produto sem controle',
            controla_estoque=False,
        )

        with self.assertRaises(ValidationError):
            self.registrar_entrada(
                produto=produto_sem_estoque
            )

    def test_registra_auditoria(self):
        resultado = self.registrar_entrada()

        auditoria = RegistroAuditoria.objects.get(
            recurso='estoque.movimentacao',
            recurso_id=str(resultado.movimentacao.uuid),
        )

        self.assertEqual(
            auditoria.matriz,
            self.matriz
        )

        self.assertEqual(
            auditoria.loja,
            self.loja
        )

        self.assertEqual(
            auditoria.acao,
            RegistroAuditoria.ACAO_CRIAR
        )

    def test_falha_na_auditoria_desfaz_toda_operacao(self):
        with patch(
            'estoque.services.movimentacoes.entradas.'
            'registrar_auditoria',
            side_effect=RuntimeError('Falha simulada de auditoria'),
        ):
            with self.assertRaises(RuntimeError):
                self.registrar_entrada()

        self.assertFalse(
            SaldoEstoque.objects.exists()
        )

        self.assertFalse(
            MovimentacaoEstoque.objects.exists()
        )

        self.assertFalse(
            RegistroAuditoria.objects.exists()
        )

    def test_atualiza_data_da_ultima_movimentacao(self):
        resultado = self.registrar_entrada()

        self.assertIsNotNone(
            resultado.saldo.ultima_movimentacao_em
        )

    def test_normaliza_campos_textuais_da_movimentacao(self):
        resultado = self.registrar_entrada(
            observacao='  Entrada conferida  ',
            documento_referencia='  NF-123  ',
            origem_id='  recebimento-1  ',
        )

        self.assertEqual(
            resultado.movimentacao.observacao,
            'Entrada conferida'
        )

        self.assertEqual(
            resultado.movimentacao.documento_referencia,
            'NF-123'
        )

        self.assertEqual(
            resultado.movimentacao.origem_id,
            'recebimento-1'
        )

