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
from estoque.services import registrar_transferencia_estoque
from produtos.models import Produto, UnidadeMedida


class RegistrarTransferenciaEstoqueTestCase(TestCase):
    def setUp(self):
        self.matriz = Matriz.objects.create(
            nome='Matriz Transferência'
        )

        self.loja_origem = Loja.objects.create(
            matriz=self.matriz,
            nome='Loja Origem',
            status=StatusOperacional.ATIVA,
        )

        self.loja_destino = Loja.objects.create(
            matriz=self.matriz,
            nome='Loja Destino',
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
            codigo_interno='TRF-001',
            nome='Produto transferência',
            controla_estoque=True,
        )

        self.saldo_origem = SaldoEstoque.objects.create(
            matriz=self.matriz,
            loja=self.loja_origem,
            produto=self.produto,
            quantidade_atual=Decimal('10.000'),
        )

    def registrar_transferencia(self, **dados):
        padrao = {
            'matriz': self.matriz,
            'loja_origem': self.loja_origem,
            'loja_destino': self.loja_destino,
            'produto': self.produto,
            'quantidade': Decimal('4.000'),
            'chave_idempotencia': 'transferencia:teste:001',
            'motivo': 'Reposição entre lojas',
        }

        padrao.update(dados)

        return registrar_transferencia_estoque(**padrao)

    def test_transferencia_cria_saida_e_entrada(self):
        resultado = self.registrar_transferencia()

        self.assertFalse(resultado.duplicada)

        self.assertEqual(
            resultado.origem.movimentacao.tipo,
            TipoMovimentacao.TRANSFERENCIA_SAIDA
        )

        self.assertEqual(
            resultado.destino.movimentacao.tipo,
            TipoMovimentacao.TRANSFERENCIA_ENTRADA
        )

        self.assertEqual(
            resultado.origem.movimentacao.natureza,
            NaturezaMovimentacao.SAIDA
        )

        self.assertEqual(
            resultado.destino.movimentacao.natureza,
            NaturezaMovimentacao.ENTRADA
        )

        self.assertEqual(
            MovimentacaoEstoque.objects.count(),
            2
        )

    def test_transferencia_atualiza_os_dois_saldos(self):
        resultado = self.registrar_transferencia()

        self.assertEqual(
            resultado.origem.saldo.quantidade_atual,
            Decimal('6.000')
        )

        self.assertEqual(
            resultado.destino.saldo.quantidade_atual,
            Decimal('4.000')
        )

    def test_transferencia_acumula_saldo_no_destino(self):
        SaldoEstoque.objects.create(
            matriz=self.matriz,
            loja=self.loja_destino,
            produto=self.produto,
            quantidade_atual=Decimal('3.000'),
        )

        resultado = self.registrar_transferencia()

        self.assertEqual(
            resultado.destino.saldo.quantidade_atual,
            Decimal('7.000')
        )

    def test_movimentacoes_compartilham_mesmo_grupo(self):
        resultado = self.registrar_transferencia()

        self.assertEqual(
            resultado.origem.movimentacao.grupo_transferencia,
            resultado.grupo_transferencia
        )

        self.assertEqual(
            resultado.destino.movimentacao.grupo_transferencia,
            resultado.grupo_transferencia
        )

    def test_transferencia_e_idempotente(self):
        primeira = self.registrar_transferencia()
        segunda = self.registrar_transferencia()

        self.assertFalse(primeira.duplicada)
        self.assertTrue(segunda.duplicada)

        self.assertEqual(
            primeira.grupo_transferencia,
            segunda.grupo_transferencia
        )

        self.assertEqual(
            MovimentacaoEstoque.objects.count(),
            2
        )

        self.saldo_origem.refresh_from_db()

        self.assertEqual(
            self.saldo_origem.quantidade_atual,
            Decimal('6.000')
        )

        saldo_destino = SaldoEstoque.objects.get(
            matriz=self.matriz,
            loja=self.loja_destino,
            produto=self.produto,
        )

        self.assertEqual(
            saldo_destino.quantidade_atual,
            Decimal('4.000')
        )

    def test_mesma_chave_com_quantidade_diferente_gera_conflito(self):
        self.registrar_transferencia()

        with self.assertRaises(ValidationError) as contexto:
            self.registrar_transferencia(
                quantidade=Decimal('2.000')
            )

        self.assertIn(
            'chave_idempotencia',
            contexto.exception.message_dict
        )

        self.assertEqual(
            MovimentacaoEstoque.objects.count(),
            2
        )

    def test_rejeita_lojas_iguais(self):
        with self.assertRaises(ValidationError) as contexto:
            self.registrar_transferencia(
                loja_destino=self.loja_origem
            )

        self.assertIn(
            'loja_destino',
            contexto.exception.message_dict
        )

    def test_rejeita_loja_origem_de_outra_matriz(self):
        outra_matriz = Matriz.objects.create(
            nome='Outra Matriz Origem'
        )

        outra_loja = Loja.objects.create(
            matriz=outra_matriz,
            nome='Outra Loja Origem',
            status=StatusOperacional.ATIVA,
        )

        with self.assertRaises(ValidationError):
            self.registrar_transferencia(
                loja_origem=outra_loja
            )

    def test_rejeita_loja_destino_de_outra_matriz(self):
        outra_matriz = Matriz.objects.create(
            nome='Outra Matriz Destino'
        )

        outra_loja = Loja.objects.create(
            matriz=outra_matriz,
            nome='Outra Loja Destino',
            status=StatusOperacional.ATIVA,
        )

        with self.assertRaises(ValidationError):
            self.registrar_transferencia(
                loja_destino=outra_loja
            )

    def test_rejeita_saldo_insuficiente_na_origem(self):
        with self.assertRaises(ValidationError):
            self.registrar_transferencia(
                quantidade=Decimal('10.001')
            )

        self.saldo_origem.refresh_from_db()

        self.assertEqual(
            self.saldo_origem.quantidade_atual,
            Decimal('10.000')
        )

        self.assertFalse(
            MovimentacaoEstoque.objects.exists()
        )

        self.assertFalse(
            SaldoEstoque.objects.filter(
                loja=self.loja_destino
            ).exists()
        )

    def test_rejeita_chave_vazia(self):
        with self.assertRaises(ValidationError) as contexto:
            self.registrar_transferencia(
                chave_idempotencia=''
            )

        self.assertIn(
            'chave_idempotencia',
            contexto.exception.message_dict
        )

    def test_rejeita_motivo_vazio(self):
        with self.assertRaises(ValidationError) as contexto:
            self.registrar_transferencia(
                motivo=''
            )

        self.assertIn(
            'motivo',
            contexto.exception.message_dict
        )

    def test_normaliza_motivo(self):
        resultado = self.registrar_transferencia(
            motivo='  Reposição urgente  '
        )

        self.assertEqual(
            resultado.origem.movimentacao.observacao,
            'Reposição urgente'
        )

        self.assertEqual(
            resultado.destino.movimentacao.observacao,
            'Reposição urgente'
        )

    def test_origem_das_movimentacoes_e_transferencia(self):
        resultado = self.registrar_transferencia()

        self.assertEqual(
            resultado.origem.movimentacao.origem,
            OrigemMovimentacao.TRANSFERENCIA
        )

        self.assertEqual(
            resultado.destino.movimentacao.origem,
            OrigemMovimentacao.TRANSFERENCIA
        )

    def test_chaves_filhas_sao_distintas(self):
        resultado = self.registrar_transferencia()

        self.assertTrue(
            resultado.origem.movimentacao.chave_idempotencia.endswith(
                ':saida'
            )
        )

        self.assertTrue(
            resultado.destino.movimentacao.chave_idempotencia.endswith(
                ':entrada'
            )
        )

        self.assertNotEqual(
            resultado.origem.movimentacao.chave_idempotencia,
            resultado.destino.movimentacao.chave_idempotencia
        )

    def test_registra_duas_auditorias(self):
        self.registrar_transferencia()

        self.assertEqual(
            RegistroAuditoria.objects.filter(
                recurso='estoque.movimentacao'
            ).count(),
            2
        )

    def test_falha_na_entrada_desfaz_toda_transferencia(self):
        with patch(
            'estoque.services.movimentacoes.entradas.'
            'registrar_auditoria',
            side_effect=RuntimeError('Falha simulada na entrada'),
        ):
            with self.assertRaises(RuntimeError):
                self.registrar_transferencia()

        self.saldo_origem.refresh_from_db()

        self.assertEqual(
            self.saldo_origem.quantidade_atual,
            Decimal('10.000')
        )

        self.assertFalse(
            MovimentacaoEstoque.objects.exists()
        )

        self.assertFalse(
            SaldoEstoque.objects.filter(
                loja=self.loja_destino
            ).exists()
        )

        self.assertFalse(
            RegistroAuditoria.objects.exists()
        )

    def test_falha_na_saida_nao_cria_entrada(self):
        with patch(
            'estoque.services.movimentacoes.saidas.'
            'registrar_auditoria',
            side_effect=RuntimeError('Falha simulada na saída'),
        ):
            with self.assertRaises(RuntimeError):
                self.registrar_transferencia()

        self.saldo_origem.refresh_from_db()

        self.assertEqual(
            self.saldo_origem.quantidade_atual,
            Decimal('10.000')
        )

        self.assertFalse(
            MovimentacaoEstoque.objects.exists()
        )

        self.assertFalse(
            SaldoEstoque.objects.filter(
                loja=self.loja_destino
            ).exists()
        )
