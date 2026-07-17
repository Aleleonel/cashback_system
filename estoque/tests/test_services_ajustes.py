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
from estoque.services import registrar_ajuste_estoque
from produtos.models import Produto, UnidadeMedida


class RegistrarAjusteEstoqueTestCase(TestCase):
    def setUp(self):
        self.matriz = Matriz.objects.create(
            nome='Matriz Service Ajuste'
        )

        self.loja = Loja.objects.create(
            matriz=self.matriz,
            nome='Loja Service Ajuste',
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
            codigo_interno='AJU-001',
            nome='Produto de ajuste',
            controla_estoque=True,
        )

    def criar_saldo(self, quantidade='10.000'):
        return SaldoEstoque.objects.create(
            matriz=self.matriz,
            loja=self.loja,
            produto=self.produto,
            quantidade_atual=Decimal(quantidade),
        )

    def registrar_ajuste(self, **dados):
        padrao = {
            'matriz': self.matriz,
            'loja': self.loja,
            'produto': self.produto,
            'origem': OrigemMovimentacao.MANUAL,
            'quantidade_ajuste': Decimal('5.000'),
            'chave_idempotencia': 'ajuste:teste:001',
            'motivo': 'Correção manual de estoque',
        }

        padrao.update(dados)

        return registrar_ajuste_estoque(**padrao)

    def test_ajuste_positivo_cria_entrada(self):
        resultado = self.registrar_ajuste()

        self.assertEqual(
            resultado.movimentacao.tipo,
            TipoMovimentacao.AJUSTE_POSITIVO
        )

        self.assertEqual(
            resultado.movimentacao.natureza,
            NaturezaMovimentacao.ENTRADA
        )

        self.assertEqual(
            resultado.movimentacao.quantidade,
            Decimal('5.000')
        )

        self.assertEqual(
            resultado.saldo.quantidade_atual,
            Decimal('5.000')
        )

    def test_ajuste_positivo_acumula_saldo_existente(self):
        self.criar_saldo()

        resultado = self.registrar_ajuste(
            quantidade_ajuste=Decimal('2.500')
        )

        self.assertEqual(
            resultado.movimentacao.saldo_anterior,
            Decimal('10.000')
        )

        self.assertEqual(
            resultado.movimentacao.saldo_posterior,
            Decimal('12.500')
        )

        self.assertEqual(
            resultado.saldo.quantidade_atual,
            Decimal('12.500')
        )

    def test_ajuste_negativo_cria_saida(self):
        self.criar_saldo()

        resultado = self.registrar_ajuste(
            quantidade_ajuste=Decimal('-4.000')
        )

        self.assertEqual(
            resultado.movimentacao.tipo,
            TipoMovimentacao.AJUSTE_NEGATIVO
        )

        self.assertEqual(
            resultado.movimentacao.natureza,
            NaturezaMovimentacao.SAIDA
        )

        self.assertEqual(
            resultado.movimentacao.quantidade,
            Decimal('4.000')
        )

        self.assertEqual(
            resultado.movimentacao.saldo_anterior,
            Decimal('10.000')
        )

        self.assertEqual(
            resultado.movimentacao.saldo_posterior,
            Decimal('6.000')
        )

    def test_ajuste_negativo_pode_zerar_saldo(self):
        self.criar_saldo()

        resultado = self.registrar_ajuste(
            quantidade_ajuste=Decimal('-10.000')
        )

        self.assertEqual(
            resultado.saldo.quantidade_atual,
            Decimal('0.000')
        )

    def test_ajuste_negativo_rejeita_saldo_insuficiente(self):
        self.criar_saldo()

        with self.assertRaises(ValidationError) as contexto:
            self.registrar_ajuste(
                quantidade_ajuste=Decimal('-10.001')
            )

        self.assertIn(
            'quantidade',
            contexto.exception.message_dict
        )

        saldo = SaldoEstoque.objects.get(
            matriz=self.matriz,
            loja=self.loja,
            produto=self.produto,
        )

        self.assertEqual(
            saldo.quantidade_atual,
            Decimal('10.000')
        )

        self.assertFalse(
            MovimentacaoEstoque.objects.exists()
        )

    def test_ajuste_negativo_rejeita_saldo_inexistente(self):
        with self.assertRaises(ValidationError) as contexto:
            self.registrar_ajuste(
                quantidade_ajuste=Decimal('-1.000')
            )

        self.assertIn(
            'saldo',
            contexto.exception.message_dict
        )

    def test_rejeita_ajuste_zero(self):
        with self.assertRaises(ValidationError) as contexto:
            self.registrar_ajuste(
                quantidade_ajuste=Decimal('0.000')
            )

        self.assertIn(
            'quantidade_ajuste',
            contexto.exception.message_dict
        )

    def test_rejeita_quantidade_invalida(self):
        with self.assertRaises(ValidationError):
            self.registrar_ajuste(
                quantidade_ajuste='valor-invalido'
            )

    def test_rejeita_quantidade_nao_finita(self):
        for quantidade in (
            'NaN',
            'Infinity',
            '-Infinity',
        ):
            with self.subTest(quantidade=quantidade):
                with self.assertRaises(ValidationError):
                    self.registrar_ajuste(
                        quantidade_ajuste=quantidade
                    )

    def test_normaliza_quantidade_para_tres_casas(self):
        resultado = self.registrar_ajuste(
            quantidade_ajuste='2.5'
        )

        self.assertEqual(
            resultado.movimentacao.quantidade,
            Decimal('2.500')
        )

    def test_motivo_e_obrigatorio(self):
        with self.assertRaises(ValidationError) as contexto:
            self.registrar_ajuste(
                motivo=''
            )

        self.assertIn(
            'motivo',
            contexto.exception.message_dict
        )

    def test_motivo_com_espacos_e_rejeitado(self):
        with self.assertRaises(ValidationError):
            self.registrar_ajuste(
                motivo='   '
            )

    def test_motivo_e_normalizado_na_observacao(self):
        resultado = self.registrar_ajuste(
            motivo='  Contagem corrigida  '
        )

        self.assertEqual(
            resultado.movimentacao.observacao,
            'Contagem corrigida'
        )

    def test_idempotencia_ajuste_positivo(self):
        primeiro = self.registrar_ajuste()
        segundo = self.registrar_ajuste()

        self.assertFalse(primeiro.duplicada)
        self.assertTrue(segundo.duplicada)

        self.assertEqual(
            primeiro.movimentacao.pk,
            segundo.movimentacao.pk
        )

        self.assertEqual(
            MovimentacaoEstoque.objects.count(),
            1
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

    def test_idempotencia_ajuste_negativo(self):
        self.criar_saldo()

        primeiro = self.registrar_ajuste(
            quantidade_ajuste=Decimal('-4.000')
        )

        segundo = self.registrar_ajuste(
            quantidade_ajuste=Decimal('-4.000')
        )

        self.assertFalse(primeiro.duplicada)
        self.assertTrue(segundo.duplicada)

        saldo = SaldoEstoque.objects.get(
            matriz=self.matriz,
            loja=self.loja,
            produto=self.produto,
        )

        self.assertEqual(
            saldo.quantidade_atual,
            Decimal('6.000')
        )

    def test_mesma_chave_com_sinal_diferente_gera_conflito(self):
        self.registrar_ajuste(
            quantidade_ajuste=Decimal('2.000')
        )

        saldo = SaldoEstoque.objects.get(
            matriz=self.matriz,
            loja=self.loja,
            produto=self.produto,
        )

        saldo.quantidade_atual = Decimal('10.000')
        saldo.save(
            update_fields=[
                'quantidade_atual',
                'atualizado_em',
            ]
        )

        with self.assertRaises(ValidationError) as contexto:
            self.registrar_ajuste(
                quantidade_ajuste=Decimal('-2.000')
            )

        self.assertIn(
            'chave_idempotencia',
            contexto.exception.message_dict
        )

        saldo.refresh_from_db()

        self.assertEqual(
            saldo.quantidade_atual,
            Decimal('10.000')
        )

        self.assertEqual(
            MovimentacaoEstoque.objects.count(),
            1
        )

    def test_mesma_chave_com_quantidade_diferente_gera_conflito(self):
        self.registrar_ajuste(
            quantidade_ajuste=Decimal('2.000')
        )

        with self.assertRaises(ValidationError) as contexto:
            self.registrar_ajuste(
                quantidade_ajuste=Decimal('3.000')
            )

        self.assertIn(
            'chave_idempotencia',
            contexto.exception.message_dict
        )

    def test_registra_auditoria_no_ajuste_positivo(self):
        resultado = self.registrar_ajuste()

        auditoria = RegistroAuditoria.objects.get(
            recurso='estoque.movimentacao',
            recurso_id=str(resultado.movimentacao.uuid),
        )

        self.assertIn(
            'Entrada de estoque',
            auditoria.descricao
        )

        self.assertIn(
            TipoMovimentacao.AJUSTE_POSITIVO,
            auditoria.descricao
        )

    def test_registra_auditoria_no_ajuste_negativo(self):
        self.criar_saldo()

        resultado = self.registrar_ajuste(
            quantidade_ajuste=Decimal('-2.000')
        )

        auditoria = RegistroAuditoria.objects.get(
            recurso='estoque.movimentacao',
            recurso_id=str(resultado.movimentacao.uuid),
        )

        self.assertIn(
            'Saída de estoque',
            auditoria.descricao
        )

        self.assertIn(
            TipoMovimentacao.AJUSTE_NEGATIVO,
            auditoria.descricao
        )

    def test_falha_na_entrada_desfaz_ajuste_positivo(self):
        with patch(
            'estoque.services.movimentacoes.entradas.'
            'registrar_auditoria',
            side_effect=RuntimeError('Falha simulada'),
        ):
            with self.assertRaises(RuntimeError):
                self.registrar_ajuste()

        self.assertFalse(
            SaldoEstoque.objects.exists()
        )

        self.assertFalse(
            MovimentacaoEstoque.objects.exists()
        )

    def test_falha_na_saida_desfaz_ajuste_negativo(self):
        self.criar_saldo()

        with patch(
            'estoque.services.movimentacoes.saidas.'
            'registrar_auditoria',
            side_effect=RuntimeError('Falha simulada'),
        ):
            with self.assertRaises(RuntimeError):
                self.registrar_ajuste(
                    quantidade_ajuste=Decimal('-2.000')
                )

        saldo = SaldoEstoque.objects.get(
            matriz=self.matriz,
            loja=self.loja,
            produto=self.produto,
        )

        self.assertEqual(
            saldo.quantidade_atual,
            Decimal('10.000')
        )

        self.assertFalse(
            MovimentacaoEstoque.objects.exists()
        )

