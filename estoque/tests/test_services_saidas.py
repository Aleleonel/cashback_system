from decimal import Decimal
from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.test import TestCase

from auditoria.models import RegistroAuditoria
from core.choices import StatusOperacional
from empresas.models import Loja, Matriz
from estoque.choices import (
    NaturezaMovimentacao,
    OrigemMovimentacao,
    TipoMovimentacao,
)
from estoque.models import MovimentacaoEstoque, SaldoEstoque
from estoque.services import registrar_saida_estoque
from produtos.models import Produto, UnidadeMedida


class RegistrarSaidaEstoqueTestCase(TestCase):
    def setUp(self):
        self.matriz = Matriz.objects.create(
            nome='Matriz Service Saída'
        )

        self.loja = Loja.objects.create(
            matriz=self.matriz,
            nome='Loja Service Saída',
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
            codigo_interno='SAI-001',
            nome='Produto de saída',
            controla_estoque=True,
        )

        self.saldo = SaldoEstoque.objects.create(
            matriz=self.matriz,
            loja=self.loja,
            produto=self.produto,
            quantidade_atual=Decimal('10.000'),
        )

    def registrar_saida(self, **dados):
        padrao = {
            'matriz': self.matriz,
            'loja': self.loja,
            'produto': self.produto,
            'tipo': TipoMovimentacao.SAIDA_MANUAL,
            'origem': OrigemMovimentacao.MANUAL,
            'quantidade': Decimal('4.000'),
            'chave_idempotencia': 'saida:teste:001',
        }

        padrao.update(dados)

        return registrar_saida_estoque(**padrao)

    def test_saida_reduz_saldo_e_cria_movimentacao(self):
        resultado = self.registrar_saida()

        self.assertFalse(resultado.duplicada)

        self.assertEqual(
            resultado.saldo.quantidade_atual,
            Decimal('6.000')
        )

        self.assertEqual(
            resultado.movimentacao.natureza,
            NaturezaMovimentacao.SAIDA
        )

        self.assertEqual(
            resultado.movimentacao.saldo_anterior,
            Decimal('10.000')
        )

        self.assertEqual(
            resultado.movimentacao.saldo_posterior,
            Decimal('6.000')
        )

        self.assertEqual(
            MovimentacaoEstoque.objects.count(),
            1
        )

    def test_saida_pode_zerar_saldo(self):
        resultado = self.registrar_saida(
            quantidade=Decimal('10.000')
        )

        self.assertEqual(
            resultado.saldo.quantidade_atual,
            Decimal('0.000')
        )

        self.assertEqual(
            resultado.movimentacao.saldo_posterior,
            Decimal('0.000')
        )

    def test_saidas_sucessivas_usam_saldo_atual(self):
        self.registrar_saida()

        resultado = self.registrar_saida(
            quantidade=Decimal('2.500'),
            chave_idempotencia='saida:teste:002',
        )

        self.assertEqual(
            resultado.movimentacao.saldo_anterior,
            Decimal('6.000')
        )

        self.assertEqual(
            resultado.movimentacao.saldo_posterior,
            Decimal('3.500')
        )

        self.assertEqual(
            resultado.saldo.quantidade_atual,
            Decimal('3.500')
        )

    def test_rejeita_saida_superior_ao_saldo(self):
        with self.assertRaises(ValidationError) as contexto:
            self.registrar_saida(
                quantidade=Decimal('10.001')
            )

        self.assertIn(
            'quantidade',
            contexto.exception.message_dict
        )

        self.saldo.refresh_from_db()

        self.assertEqual(
            self.saldo.quantidade_atual,
            Decimal('10.000')
        )

        self.assertFalse(
            MovimentacaoEstoque.objects.exists()
        )

    def test_rejeita_saida_quando_saldo_nao_existe(self):
        self.saldo.delete()

        with self.assertRaises(ValidationError) as contexto:
            self.registrar_saida()

        self.assertIn(
            'saldo',
            contexto.exception.message_dict
        )

        self.assertFalse(
            MovimentacaoEstoque.objects.exists()
        )

    def test_idempotencia_nao_aplica_saida_duas_vezes(self):
        primeiro = self.registrar_saida()
        segundo = self.registrar_saida()

        self.assertFalse(primeiro.duplicada)
        self.assertTrue(segundo.duplicada)

        self.assertEqual(
            primeiro.movimentacao.pk,
            segundo.movimentacao.pk
        )

        self.saldo.refresh_from_db()

        self.assertEqual(
            self.saldo.quantidade_atual,
            Decimal('6.000')
        )

        self.assertEqual(
            MovimentacaoEstoque.objects.count(),
            1
        )

    def test_mesma_chave_com_quantidade_diferente_gera_conflito(self):
        self.registrar_saida()

        with self.assertRaises(ValidationError) as contexto:
            self.registrar_saida(
                quantidade=Decimal('2.000')
            )

        self.assertIn(
            'chave_idempotencia',
            contexto.exception.message_dict
        )

        self.saldo.refresh_from_db()

        self.assertEqual(
            self.saldo.quantidade_atual,
            Decimal('6.000')
        )

        self.assertEqual(
            MovimentacaoEstoque.objects.count(),
            1
        )

    def test_mesma_chave_com_produto_diferente_gera_conflito(self):
        self.registrar_saida()

        outro_produto = Produto.objects.create(
            matriz=self.matriz,
            unidade_medida=self.unidade,
            codigo_interno='SAI-002',
            nome='Segundo produto de saída',
            controla_estoque=True,
        )

        SaldoEstoque.objects.create(
            matriz=self.matriz,
            loja=self.loja,
            produto=outro_produto,
            quantidade_atual=Decimal('20.000'),
        )

        with self.assertRaises(ValidationError) as contexto:
            self.registrar_saida(
                produto=outro_produto
            )

        self.assertIn(
            'chave_idempotencia',
            contexto.exception.message_dict
        )

        saldo_outro_produto = SaldoEstoque.objects.get(
            produto=outro_produto
        )

        self.assertEqual(
            saldo_outro_produto.quantidade_atual,
            Decimal('20.000')
        )

    def test_exige_chave_de_idempotencia(self):
        with self.assertRaises(ValidationError) as contexto:
            self.registrar_saida(
                chave_idempotencia=''
            )

        self.assertIn(
            'chave_idempotencia',
            contexto.exception.message_dict
        )

    def test_rejeita_quantidade_zero(self):
        with self.assertRaises(ValidationError):
            self.registrar_saida(
                quantidade=Decimal('0.000')
            )

    def test_rejeita_quantidade_negativa(self):
        with self.assertRaises(ValidationError):
            self.registrar_saida(
                quantidade=Decimal('-1.000')
            )

    def test_rejeita_quantidade_invalida(self):
        with self.assertRaises(ValidationError):
            self.registrar_saida(
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
                    self.registrar_saida(
                        quantidade=quantidade
                    )

    def test_normaliza_quantidade_para_tres_casas(self):
        resultado = self.registrar_saida(
            quantidade='2.5'
        )

        self.assertEqual(
            resultado.movimentacao.quantidade,
            Decimal('2.500')
        )

        self.assertEqual(
            resultado.saldo.quantidade_atual,
            Decimal('7.500')
        )

    def test_rejeita_tipo_de_entrada(self):
        with self.assertRaises(ValidationError) as contexto:
            self.registrar_saida(
                tipo=TipoMovimentacao.ENTRADA_MANUAL
            )

        self.assertIn(
            'tipo',
            contexto.exception.message_dict
        )

    def test_rejeita_loja_de_outra_matriz(self):
        outra_matriz = Matriz.objects.create(
            nome='Outra Matriz Saída'
        )

        outra_loja = Loja.objects.create(
            matriz=outra_matriz,
            nome='Outra Loja Saída',
            status=StatusOperacional.ATIVA,
        )

        with self.assertRaises(ValidationError):
            self.registrar_saida(
                loja=outra_loja
            )

    def test_rejeita_produto_de_outra_matriz(self):
        outra_matriz = Matriz.objects.create(
            nome='Matriz Outro Produto Saída'
        )

        outra_unidade = UnidadeMedida.objects.create(
            matriz=outra_matriz,
            sigla='CX',
            descricao='Caixa',
        )

        outro_produto = Produto.objects.create(
            matriz=outra_matriz,
            unidade_medida=outra_unidade,
            codigo_interno='SAI-OUT-001',
            nome='Produto de outra matriz',
            controla_estoque=True,
        )

        with self.assertRaises(ValidationError):
            self.registrar_saida(
                produto=outro_produto
            )

    def test_rejeita_produto_sem_controle_de_estoque(self):
        produto_sem_estoque = Produto.objects.create(
            matriz=self.matriz,
            unidade_medida=self.unidade,
            codigo_interno='SAI-SEM-001',
            nome='Produto sem controle',
            controla_estoque=False,
        )

        with self.assertRaises(ValidationError):
            self.registrar_saida(
                produto=produto_sem_estoque
            )

    def test_registra_auditoria(self):
        resultado = self.registrar_saida()

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

        self.assertIn(
            'Saída de estoque',
            auditoria.descricao
        )

    def test_falha_na_auditoria_desfaz_toda_operacao(self):
        with patch(
            'estoque.services.movimentacoes.saidas.'
            'registrar_auditoria',
            side_effect=RuntimeError('Falha simulada de auditoria'),
        ):
            with self.assertRaises(RuntimeError):
                self.registrar_saida()

        self.saldo.refresh_from_db()

        self.assertEqual(
            self.saldo.quantidade_atual,
            Decimal('10.000')
        )

        self.assertFalse(
            MovimentacaoEstoque.objects.exists()
        )

        self.assertFalse(
            RegistroAuditoria.objects.exists()
        )

    def test_atualiza_data_da_ultima_movimentacao(self):
        resultado = self.registrar_saida()

        self.assertIsNotNone(
            resultado.saldo.ultima_movimentacao_em
        )

    def test_normaliza_campos_textuais_da_movimentacao(self):
        resultado = self.registrar_saida(
            observacao='  Saída conferida  ',
            documento_referencia='  VENDA-123  ',
            origem_id='  item-venda-1  ',
        )

        self.assertEqual(
            resultado.movimentacao.observacao,
            'Saída conferida'
        )

        self.assertEqual(
            resultado.movimentacao.documento_referencia,
            'VENDA-123'
        )

        self.assertEqual(
            resultado.movimentacao.origem_id,
            'item-venda-1'
        )
