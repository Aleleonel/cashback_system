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
from estoque.services import liberar_reserva_estoque
from produtos.models import Produto, UnidadeMedida


class LiberarReservaEstoqueTestCase(TestCase):
    def setUp(self):
        self.matriz = Matriz.objects.create(
            nome='Matriz Liberacao Reserva'
        )
        self.loja = Loja.objects.create(
            matriz=self.matriz,
            nome='Loja Liberacao Reserva',
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
            codigo_interno='LIB-RES-001',
            nome='Produto Liberacao Reserva',
            controla_estoque=True,
        )
        self.saldo = SaldoEstoque.objects.create(
            matriz=self.matriz,
            loja=self.loja,
            produto=self.produto,
            quantidade_atual=Decimal('10.000'),
        )
        self.reserva = ReservaEstoque.objects.create(
            matriz=self.matriz,
            loja=self.loja,
            produto=self.produto,
            quantidade=Decimal('4.000'),
            origem=OrigemMovimentacao.VENDA,
            chave_idempotencia='reserva:liberacao:001',
        )

    def liberar(self):
        return liberar_reserva_estoque(reserva=self.reserva)

    def test_libera_reserva_ativa(self):
        resultado = self.liberar()
        self.assertFalse(resultado.duplicada)
        self.assertEqual(
            resultado.reserva.status,
            StatusReservaEstoque.LIBERADA,
        )
        self.assertIsNotNone(resultado.reserva.liberada_em)

    def test_restitui_saldo_disponivel_sem_alterar_fisico(self):
        self.assertEqual(
            get_saldo_disponivel(
                matriz=self.matriz,
                loja=self.loja,
                produto=self.produto,
            ),
            Decimal('6.000'),
        )
        self.liberar()
        self.saldo.refresh_from_db()
        self.assertEqual(self.saldo.quantidade_atual, Decimal('10.000'))
        self.assertEqual(
            get_saldo_disponivel(
                matriz=self.matriz,
                loja=self.loja,
                produto=self.produto,
            ),
            Decimal('10.000'),
        )

    def test_liberacao_repetida_e_idempotente(self):
        primeiro = self.liberar()
        segundo = self.liberar()
        self.assertFalse(primeiro.duplicada)
        self.assertTrue(segundo.duplicada)
        self.assertEqual(primeiro.reserva.pk, segundo.reserva.pk)
        self.assertEqual(
            primeiro.reserva.liberada_em,
            segundo.reserva.liberada_em,
        )

    def test_liberacao_repetida_nao_duplica_auditoria(self):
        self.liberar()
        self.liberar()
        self.assertEqual(
            RegistroAuditoria.objects.filter(
                recurso='estoque.reserva',
                recurso_id=str(self.reserva.uuid),
                acao=RegistroAuditoria.ACAO_EDITAR,
            ).count(),
            1,
        )

    def test_registra_auditoria(self):
        resultado = self.liberar()
        auditoria = RegistroAuditoria.objects.get(
            recurso='estoque.reserva',
            recurso_id=str(resultado.reserva.uuid),
            acao=RegistroAuditoria.ACAO_EDITAR,
        )
        self.assertEqual(auditoria.matriz, self.matriz)
        self.assertEqual(auditoria.loja, self.loja)
        self.assertIn('LiberaÃ§Ã£o de reserva', auditoria.descricao)
        self.assertIn('saldo_disponivel_anterior=6.000', auditoria.descricao)
        self.assertIn('saldo_disponivel_posterior=10.000', auditoria.descricao)

    def test_falha_na_auditoria_desfaz_liberacao(self):
        with patch(
            'estoque.services.movimentacoes.liberacoes.registrar_auditoria',
            side_effect=RuntimeError('Falha simulada de auditoria'),
        ):
            with self.assertRaises(RuntimeError):
                self.liberar()
        self.reserva.refresh_from_db()
        self.assertEqual(self.reserva.status, StatusReservaEstoque.ATIVA)
        self.assertIsNone(self.reserva.liberada_em)
        self.assertEqual(
            get_saldo_disponivel(
                matriz=self.matriz,
                loja=self.loja,
                produto=self.produto,
            ),
            Decimal('6.000'),
        )

    def test_rejeita_estados_encerrados_nao_liberados(self):
        casos = (
            (StatusReservaEstoque.CONFIRMADA, 'confirmada_em'),
            (StatusReservaEstoque.CANCELADA, 'cancelada_em'),
            (StatusReservaEstoque.EXPIRADA, 'expirada_em'),
        )
        for status, campo_data in casos:
            with self.subTest(status=status):
                reserva = ReservaEstoque.objects.create(
                    matriz=self.matriz,
                    loja=self.loja,
                    produto=self.produto,
                    quantidade=Decimal('1.000'),
                    origem=OrigemMovimentacao.VENDA,
                    chave_idempotencia=f'reserva:{status}',
                    status=status,
                    **{campo_data: timezone.now()},
                )
                with self.assertRaises(ValidationError) as contexto:
                    liberar_reserva_estoque(reserva=reserva)
                self.assertIn('status', contexto.exception.message_dict)

    def test_utiliza_estado_atual_do_banco(self):
        instancia_desatualizada = ReservaEstoque.objects.get(pk=self.reserva.pk)
        primeiro = liberar_reserva_estoque(reserva=instancia_desatualizada)
        segundo = liberar_reserva_estoque(reserva=self.reserva)
        self.assertFalse(primeiro.duplicada)
        self.assertTrue(segundo.duplicada)
