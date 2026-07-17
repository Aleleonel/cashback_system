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
from estoque.services import (
    registrar_entrada_estoque,
    registrar_reversao_estoque,
    registrar_saida_estoque,
)
from produtos.models import Produto, UnidadeMedida


class RegistrarReversaoEstoqueTestCase(TestCase):
    def setUp(self):
        self.matriz = Matriz.objects.create(
            nome='Matriz Service Reversao'
        )

        self.loja = Loja.objects.create(
            matriz=self.matriz,
            nome='Loja Service Reversao',
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
            codigo_interno='REV-001',
            nome='Produto para reversao',
            controla_estoque=True,
        )

    def registrar_entrada_original(
        self,
        *,
        quantidade=Decimal('10.000'),
        chave='reversao:entrada-original',
    ):
        return registrar_entrada_estoque(
            matriz=self.matriz,
            loja=self.loja,
            produto=self.produto,
            tipo=TipoMovimentacao.ENTRADA_MANUAL,
            origem=OrigemMovimentacao.MANUAL,
            quantidade=quantidade,
            chave_idempotencia=chave,
            observacao='Entrada original',
        )

    def registrar_saida_original(
        self,
        *,
        quantidade=Decimal('4.000'),
        chave='reversao:saida-original',
    ):
        return registrar_saida_estoque(
            matriz=self.matriz,
            loja=self.loja,
            produto=self.produto,
            tipo=TipoMovimentacao.SAIDA_MANUAL,
            origem=OrigemMovimentacao.MANUAL,
            quantidade=quantidade,
            chave_idempotencia=chave,
            observacao='Saida original',
        )

    def registrar_reversao(
        self,
        *,
        movimentacao_origem,
        chave='reversao:teste:001',
        motivo='Cancelamento da operacao',
        **dados,
    ):
        padrao = {
            'movimentacao_origem': movimentacao_origem,
            'chave_idempotencia': chave,
            'motivo': motivo,
        }

        padrao.update(dados)

        return registrar_reversao_estoque(**padrao)

    def test_reversao_de_entrada_gera_saida(self):
        entrada = self.registrar_entrada_original()

        resultado = self.registrar_reversao(
            movimentacao_origem=entrada.movimentacao
        )

        self.assertFalse(resultado.duplicada)

        self.assertEqual(
            resultado.movimentacao.tipo,
            TipoMovimentacao.REVERSAO_SAIDA
        )

        self.assertEqual(
            resultado.movimentacao.natureza,
            NaturezaMovimentacao.SAIDA
        )

        self.assertEqual(
            resultado.movimentacao.movimentacao_origem,
            entrada.movimentacao
        )

        self.assertEqual(
            resultado.movimentacao.quantidade,
            Decimal('10.000')
        )

        self.assertEqual(
            resultado.saldo.quantidade_atual,
            Decimal('0.000')
        )

    def test_reversao_de_saida_gera_entrada(self):
        self.registrar_entrada_original()

        saida = self.registrar_saida_original()

        resultado = self.registrar_reversao(
            movimentacao_origem=saida.movimentacao
        )

        self.assertFalse(resultado.duplicada)

        self.assertEqual(
            resultado.movimentacao.tipo,
            TipoMovimentacao.REVERSAO_ENTRADA
        )

        self.assertEqual(
            resultado.movimentacao.natureza,
            NaturezaMovimentacao.ENTRADA
        )

        self.assertEqual(
            resultado.movimentacao.movimentacao_origem,
            saida.movimentacao
        )

        self.assertEqual(
            resultado.movimentacao.quantidade,
            Decimal('4.000')
        )

        self.assertEqual(
            resultado.saldo.quantidade_atual,
            Decimal('10.000')
        )

    def test_reversao_e_idempotente(self):
        entrada = self.registrar_entrada_original()

        primeira = self.registrar_reversao(
            movimentacao_origem=entrada.movimentacao
        )

        segunda = self.registrar_reversao(
            movimentacao_origem=entrada.movimentacao
        )

        self.assertFalse(primeira.duplicada)
        self.assertTrue(segunda.duplicada)

        self.assertEqual(
            primeira.movimentacao.pk,
            segunda.movimentacao.pk
        )

        self.assertEqual(
            MovimentacaoEstoque.objects.count(),
            2
        )

        saldo = SaldoEstoque.objects.get(
            matriz=self.matriz,
            loja=self.loja,
            produto=self.produto,
        )

        self.assertEqual(
            saldo.quantidade_atual,
            Decimal('0.000')
        )

    def test_mesma_origem_com_nova_chave_e_rejeitada(self):
        entrada = self.registrar_entrada_original()

        self.registrar_reversao(
            movimentacao_origem=entrada.movimentacao
        )

        with self.assertRaises(ValidationError) as contexto:
            self.registrar_reversao(
                movimentacao_origem=entrada.movimentacao,
                chave='reversao:teste:outra-chave',
            )

        self.assertIn(
            'movimentacao_origem',
            contexto.exception.message_dict
        )

        self.assertEqual(
            MovimentacaoEstoque.objects.count(),
            2
        )

    def test_mesma_chave_com_motivo_diferente_e_rejeitada(self):
        entrada = self.registrar_entrada_original()

        self.registrar_reversao(
            movimentacao_origem=entrada.movimentacao
        )

        with self.assertRaises(ValidationError) as contexto:
            self.registrar_reversao(
                movimentacao_origem=entrada.movimentacao,
                motivo='Outro motivo',
            )

        self.assertIn(
            'chave_idempotencia',
            contexto.exception.message_dict
        )

    def test_nao_permite_reverter_uma_reversao(self):
        entrada = self.registrar_entrada_original()

        primeira_reversao = self.registrar_reversao(
            movimentacao_origem=entrada.movimentacao
        )

        with self.assertRaises(ValidationError) as contexto:
            self.registrar_reversao(
                movimentacao_origem=primeira_reversao.movimentacao,
                chave='reversao:da-reversao',
            )

        self.assertIn(
            'movimentacao_origem',
            contexto.exception.message_dict
        )

        self.assertEqual(
            MovimentacaoEstoque.objects.count(),
            2
        )

    def test_exige_chave_de_idempotencia(self):
        entrada = self.registrar_entrada_original()

        with self.assertRaises(ValidationError) as contexto:
            self.registrar_reversao(
                movimentacao_origem=entrada.movimentacao,
                chave='',
            )

        self.assertIn(
            'chave_idempotencia',
            contexto.exception.message_dict
        )

    def test_exige_motivo(self):
        entrada = self.registrar_entrada_original()

        with self.assertRaises(ValidationError) as contexto:
            self.registrar_reversao(
                movimentacao_origem=entrada.movimentacao,
                motivo='',
            )

        self.assertIn(
            'motivo',
            contexto.exception.message_dict
        )

    def test_rejeita_movimentacao_sem_pk(self):
        movimentacao = MovimentacaoEstoque()

        with self.assertRaises(ValidationError) as contexto:
            self.registrar_reversao(
                movimentacao_origem=movimentacao
            )

        self.assertIn(
            'movimentacao_origem',
            contexto.exception.message_dict
        )

    def test_reversao_de_entrada_exige_saldo_suficiente(self):
        entrada = self.registrar_entrada_original()

        self.registrar_saida_original(
            quantidade=Decimal('8.000'),
            chave='reversao:consumo-parcial',
        )

        with self.assertRaises(ValidationError) as contexto:
            self.registrar_reversao(
                movimentacao_origem=entrada.movimentacao
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
            Decimal('2.000')
        )

        self.assertEqual(
            MovimentacaoEstoque.objects.count(),
            2
        )

    def test_normaliza_campos_textuais(self):
        entrada = self.registrar_entrada_original()

        resultado = self.registrar_reversao(
            movimentacao_origem=entrada.movimentacao,
            motivo='  Cancelamento conferido  ',
            documento_referencia='  DOC-REV-001  ',
            origem_id='  operacao-reversao-1  ',
        )

        self.assertEqual(
            resultado.movimentacao.observacao,
            'Cancelamento conferido'
        )

        self.assertEqual(
            resultado.movimentacao.documento_referencia,
            'DOC-REV-001'
        )

        self.assertEqual(
            resultado.movimentacao.origem_id,
            'operacao-reversao-1'
        )

        self.assertEqual(
            resultado.movimentacao.origem,
            OrigemMovimentacao.SISTEMA
        )

    def test_origem_id_padrao_e_uuid_da_movimentacao_original(self):
        entrada = self.registrar_entrada_original()

        resultado = self.registrar_reversao(
            movimentacao_origem=entrada.movimentacao
        )

        self.assertEqual(
            resultado.movimentacao.origem_id,
            str(entrada.movimentacao.uuid)
        )

    def test_registra_auditoria_da_reversao(self):
        entrada = self.registrar_entrada_original()

        resultado = self.registrar_reversao(
            movimentacao_origem=entrada.movimentacao
        )

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
            'Saída de estoque'.lower(),
            auditoria.descricao.lower()
        )

    def test_falha_na_auditoria_desfaz_reversao(self):
        entrada = self.registrar_entrada_original()

        with patch(
            'estoque.services.movimentacoes.saidas.'
            'registrar_auditoria',
            side_effect=RuntimeError(
                'Falha simulada na auditoria da reversao'
            ),
        ):
            with self.assertRaises(RuntimeError):
                self.registrar_reversao(
                    movimentacao_origem=entrada.movimentacao
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

        self.assertEqual(
            MovimentacaoEstoque.objects.count(),
            1
        )

        self.assertFalse(
            MovimentacaoEstoque.objects.filter(
                movimentacao_origem=entrada.movimentacao
            ).exists()
        )

        self.assertEqual(
            RegistroAuditoria.objects.count(),
            1
        )
