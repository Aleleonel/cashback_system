from decimal import Decimal
from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from auditoria.models import RegistroAuditoria
from core.choices import StatusOperacional
from empresas.models import Loja, Matriz
from estoque.choices import OrigemMovimentacao, StatusReservaEstoque
from estoque.models import ReservaEstoque, SaldoEstoque
from estoque.selectors import get_saldo_disponivel
from estoque.services import registrar_reserva_estoque
from produtos.models import Produto, UnidadeMedida


class RegistrarReservaEstoqueTestCase(TestCase):
    def setUp(self):
        self.matriz = Matriz.objects.create(
            nome='Matriz Service Reserva'
        )

        self.loja = Loja.objects.create(
            matriz=self.matriz,
            nome='Loja Service Reserva',
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
            codigo_interno='SRV-RES-001',
            nome='Produto Service Reserva',
            controla_estoque=True,
        )

        self.saldo = SaldoEstoque.objects.create(
            matriz=self.matriz,
            loja=self.loja,
            produto=self.produto,
            quantidade_atual=Decimal('10.000'),
        )

    def registrar_reserva(self, **dados):
        padrao = {
            'matriz': self.matriz,
            'loja': self.loja,
            'produto': self.produto,
            'origem': OrigemMovimentacao.VENDA,
            'quantidade': Decimal('4.000'),
            'chave_idempotencia': 'reserva:service:001',
        }

        padrao.update(dados)

        return registrar_reserva_estoque(**padrao)

    def test_cria_reserva_ativa_sem_alterar_saldo_fisico(self):
        resultado = self.registrar_reserva()

        self.assertFalse(resultado.duplicada)
        self.assertEqual(
            resultado.reserva.status,
            StatusReservaEstoque.ATIVA
        )
        self.assertEqual(
            resultado.reserva.quantidade,
            Decimal('4.000')
        )

        self.saldo.refresh_from_db()

        self.assertEqual(
            self.saldo.quantidade_atual,
            Decimal('10.000')
        )
        self.assertEqual(
            get_saldo_disponivel(
                matriz=self.matriz,
                loja=self.loja,
                produto=self.produto,
            ),
            Decimal('6.000')
        )

    def test_reservas_sucessivas_usam_saldo_disponivel(self):
        self.registrar_reserva()

        segundo = self.registrar_reserva(
            quantidade=Decimal('3.500'),
            chave_idempotencia='reserva:service:002',
        )

        self.assertFalse(segundo.duplicada)
        self.assertEqual(
            get_saldo_disponivel(
                matriz=self.matriz,
                loja=self.loja,
                produto=self.produto,
            ),
            Decimal('2.500')
        )

    def test_permite_reservar_exatamente_o_disponivel(self):
        resultado = self.registrar_reserva(
            quantidade=Decimal('10.000')
        )

        self.assertFalse(resultado.duplicada)
        self.assertEqual(
            get_saldo_disponivel(
                matriz=self.matriz,
                loja=self.loja,
                produto=self.produto,
            ),
            Decimal('0.000')
        )

    def test_rejeita_reserva_superior_ao_disponivel(self):
        self.registrar_reserva()

        with self.assertRaises(ValidationError) as contexto:
            self.registrar_reserva(
                quantidade=Decimal('6.001'),
                chave_idempotencia='reserva:service:002',
            )

        self.assertIn(
            'quantidade',
            contexto.exception.message_dict
        )
        self.assertEqual(
            ReservaEstoque.objects.count(),
            1
        )

    def test_rejeita_reserva_quando_saldo_nao_existe(self):
        self.saldo.delete()

        with self.assertRaises(ValidationError) as contexto:
            self.registrar_reserva()

        self.assertIn(
            'quantidade',
            contexto.exception.message_dict
        )
        self.assertFalse(
            ReservaEstoque.objects.exists()
        )

    def test_idempotencia_nao_cria_reserva_duas_vezes(self):
        primeiro = self.registrar_reserva()
        segundo = self.registrar_reserva()

        self.assertFalse(primeiro.duplicada)
        self.assertTrue(segundo.duplicada)
        self.assertEqual(
            primeiro.reserva.pk,
            segundo.reserva.pk
        )
        self.assertEqual(
            ReservaEstoque.objects.count(),
            1
        )

    def test_mesma_chave_com_quantidade_diferente_gera_conflito(self):
        self.registrar_reserva()

        with self.assertRaises(ValidationError) as contexto:
            self.registrar_reserva(
                quantidade=Decimal('3.000')
            )

        self.assertIn(
            'chave_idempotencia',
            contexto.exception.message_dict
        )
        self.assertEqual(
            ReservaEstoque.objects.count(),
            1
        )

    def test_mesma_chave_com_produto_diferente_gera_conflito(self):
        self.registrar_reserva()

        outro_produto = Produto.objects.create(
            matriz=self.matriz,
            unidade_medida=self.unidade,
            codigo_interno='SRV-RES-002',
            nome='Outro Produto Service Reserva',
            controla_estoque=True,
        )

        SaldoEstoque.objects.create(
            matriz=self.matriz,
            loja=self.loja,
            produto=outro_produto,
            quantidade_atual=Decimal('20.000'),
        )

        with self.assertRaises(ValidationError) as contexto:
            self.registrar_reserva(
                produto=outro_produto
            )

        self.assertIn(
            'chave_idempotencia',
            contexto.exception.message_dict
        )
        self.assertEqual(
            ReservaEstoque.objects.count(),
            1
        )

    def test_exige_chave_de_idempotencia(self):
        with self.assertRaises(ValidationError) as contexto:
            self.registrar_reserva(
                chave_idempotencia=''
            )

        self.assertIn(
            'chave_idempotencia',
            contexto.exception.message_dict
        )

    def test_rejeita_quantidades_invalidas(self):
        for quantidade in (
            Decimal('0.000'),
            Decimal('-1.000'),
            'quantidade-invalida',
            'NaN',
            'Infinity',
            '-Infinity',
        ):
            with self.subTest(quantidade=quantidade):
                with self.assertRaises(ValidationError):
                    self.registrar_reserva(
                        quantidade=quantidade
                    )

    def test_normaliza_quantidade_para_tres_casas(self):
        resultado = self.registrar_reserva(
            quantidade='2.5'
        )

        self.assertEqual(
            resultado.reserva.quantidade,
            Decimal('2.500')
        )

    def test_rejeita_contexto_incompativel(self):
        outra_matriz = Matriz.objects.create(
            nome='Outra Matriz Service Reserva'
        )

        outra_loja = Loja.objects.create(
            matriz=outra_matriz,
            nome='Outra Loja Service Reserva',
            status=StatusOperacional.ATIVA,
        )

        with self.assertRaises(ValidationError) as contexto:
            self.registrar_reserva(
                loja=outra_loja
            )

        self.assertIn(
            'loja',
            contexto.exception.message_dict
        )

    def test_rejeita_produto_sem_controle_de_estoque(self):
        produto = Produto.objects.create(
            matriz=self.matriz,
            unidade_medida=self.unidade,
            codigo_interno='SRV-RES-SEM',
            nome='Produto sem controle',
            controla_estoque=False,
        )

        with self.assertRaises(ValidationError) as contexto:
            self.registrar_reserva(
                produto=produto
            )

        self.assertIn(
            'produto',
            contexto.exception.message_dict
        )

    def test_normaliza_campos_textuais_e_preserva_expiracao(self):
        expira_em = timezone.now()

        resultado = self.registrar_reserva(
            origem_id='  item-venda-1  ',
            documento_referencia='  VENDA-123  ',
            expira_em=expira_em,
        )

        self.assertEqual(
            resultado.reserva.origem_id,
            'item-venda-1'
        )
        self.assertEqual(
            resultado.reserva.documento_referencia,
            'VENDA-123'
        )
        self.assertEqual(
            resultado.reserva.expira_em,
            expira_em
        )

    def test_registra_auditoria(self):
        resultado = self.registrar_reserva()

        auditoria = RegistroAuditoria.objects.get(
            recurso='estoque.reserva',
            recurso_id=str(resultado.reserva.uuid),
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
            'Reserva de estoque',
            auditoria.descricao
        )

    def test_reprocessamento_idempotente_nao_duplica_auditoria(self):
        self.registrar_reserva()
        self.registrar_reserva()

        self.assertEqual(
            RegistroAuditoria.objects.filter(
                recurso='estoque.reserva'
            ).count(),
            1
        )

    def test_falha_na_auditoria_desfaz_reserva(self):
        with patch(
            'estoque.services.movimentacoes.reservas.'
            'registrar_auditoria',
            side_effect=RuntimeError('Falha simulada de auditoria'),
        ):
            with self.assertRaises(RuntimeError):
                self.registrar_reserva()

        self.assertFalse(
            ReservaEstoque.objects.exists()
        )
        self.assertFalse(
            RegistroAuditoria.objects.exists()
        )

        self.saldo.refresh_from_db()

        self.assertEqual(
            self.saldo.quantidade_atual,
            Decimal('10.000')
        )
