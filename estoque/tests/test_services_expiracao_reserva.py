from decimal import Decimal
from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from core.choices import StatusOperacional
from empresas.models import Loja, Matriz
from estoque.choices import OrigemMovimentacao, StatusReservaEstoque
from estoque.models import ReservaEstoque, SaldoEstoque
from estoque.services import expirar_reserva_estoque
from produtos.models import Produto, UnidadeMedida


class ExpirarReservaEstoqueTestCase(TestCase):
    def setUp(self):
        self.matriz = Matriz.objects.create(
            nome='Matriz Expiração'
        )

        self.loja = Loja.objects.create(
            matriz=self.matriz,
            nome='Loja Expiração',
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
            codigo_interno='EXP-001',
            nome='Produto Expiração',
            controla_estoque=True,
        )

        self.saldo = SaldoEstoque.objects.create(
            matriz=self.matriz,
            loja=self.loja,
            produto=self.produto,
            quantidade_atual=Decimal('10.000'),
        )

        self.agora = timezone.now()

    def criar_reserva(
        self,
        *,
        status=StatusReservaEstoque.ATIVA,
        expira_em=None,
        chave='expiracao:001',
    ):
        dados = {
            'matriz': self.matriz,
            'loja': self.loja,
            'produto': self.produto,
            'quantidade': Decimal('3.000'),
            'status': status,
            'origem': OrigemMovimentacao.VENDA,
            'chave_idempotencia': chave,
            'expira_em': expira_em,
        }

        if status == StatusReservaEstoque.CONFIRMADA:
            dados['confirmada_em'] = self.agora

        if status == StatusReservaEstoque.LIBERADA:
            dados['liberada_em'] = self.agora

        if status == StatusReservaEstoque.CANCELADA:
            dados['cancelada_em'] = self.agora

        if status == StatusReservaEstoque.EXPIRADA:
            dados['expirada_em'] = self.agora

        return ReservaEstoque.objects.create(**dados)

    def test_expira_reserva_ativa_vencida(self):
        reserva = self.criar_reserva(
            expira_em=self.agora - timezone.timedelta(minutes=1)
        )

        resultado = expirar_reserva_estoque(
            reserva=reserva,
            agora=self.agora,
        )

        resultado.reserva.refresh_from_db()

        self.assertEqual(
            resultado.reserva.status,
            StatusReservaEstoque.EXPIRADA,
        )
        self.assertEqual(
            resultado.reserva.expirada_em,
            self.agora,
        )
        self.assertFalse(resultado.duplicada)

    def test_expiracao_restitui_disponibilidade(self):
        reserva = self.criar_reserva(
            expira_em=self.agora - timezone.timedelta(minutes=1)
        )

        saldo_fisico_anterior = self.saldo.quantidade_atual

        expirar_reserva_estoque(
            reserva=reserva,
            agora=self.agora,
        )

        self.saldo.refresh_from_db()

        self.assertEqual(
            self.saldo.quantidade_atual,
            saldo_fisico_anterior,
        )

        reservas_ativas = ReservaEstoque.objects.filter(
            matriz=self.matriz,
            loja=self.loja,
            produto=self.produto,
            status=StatusReservaEstoque.ATIVA,
        ).count()

        self.assertEqual(reservas_ativas, 0)

    def test_expiracao_repetida_e_idempotente(self):
        reserva = self.criar_reserva(
            expira_em=self.agora - timezone.timedelta(minutes=1)
        )

        primeiro = expirar_reserva_estoque(
            reserva=reserva,
            agora=self.agora,
        )

        segundo = expirar_reserva_estoque(
            reserva=reserva,
            agora=self.agora + timezone.timedelta(minutes=1),
        )

        self.assertFalse(primeiro.duplicada)
        self.assertTrue(segundo.duplicada)
        self.assertEqual(
            primeiro.reserva.expirada_em,
            segundo.reserva.expirada_em,
        )

    def test_expiracao_repetida_nao_duplica_auditoria(self):
        reserva = self.criar_reserva(
            expira_em=self.agora - timezone.timedelta(minutes=1)
        )

        with patch(
            'estoque.services.movimentacoes.expiracoes.'
            'registrar_auditoria'
        ) as auditoria:
            expirar_reserva_estoque(
                reserva=reserva,
                agora=self.agora,
            )

            expirar_reserva_estoque(
                reserva=reserva,
                agora=self.agora,
            )

        auditoria.assert_called_once()

    def test_rejeita_reserva_sem_data_de_expiracao(self):
        reserva = self.criar_reserva(
            expira_em=None
        )

        with self.assertRaises(ValidationError) as contexto:
            expirar_reserva_estoque(
                reserva=reserva,
                agora=self.agora,
            )

        self.assertIn(
            'expira_em',
            contexto.exception.message_dict,
        )

    def test_rejeita_expiracao_antecipada(self):
        reserva = self.criar_reserva(
            expira_em=self.agora + timezone.timedelta(minutes=1)
        )

        with self.assertRaises(ValidationError) as contexto:
            expirar_reserva_estoque(
                reserva=reserva,
                agora=self.agora,
            )

        self.assertIn(
            'expira_em',
            contexto.exception.message_dict,
        )

    def test_rejeita_estados_encerrados_nao_expirados(self):
        estados = [
            StatusReservaEstoque.CONFIRMADA,
            StatusReservaEstoque.LIBERADA,
            StatusReservaEstoque.CANCELADA,
        ]

        for indice, status in enumerate(estados, start=1):
            with self.subTest(status=status):
                reserva = self.criar_reserva(
                    status=status,
                    expira_em=(
                        self.agora
                        - timezone.timedelta(minutes=1)
                    ),
                    chave=f'expiracao:encerrada:{indice}',
                )

                with self.assertRaises(ValidationError):
                    expirar_reserva_estoque(
                        reserva=reserva,
                        agora=self.agora,
                    )

    def test_falha_na_auditoria_desfaz_expiracao(self):
        reserva = self.criar_reserva(
            expira_em=self.agora - timezone.timedelta(minutes=1)
        )

        with patch(
            'estoque.services.movimentacoes.expiracoes.'
            'registrar_auditoria',
            side_effect=RuntimeError('Falha simulada'),
        ):
            with self.assertRaises(RuntimeError):
                expirar_reserva_estoque(
                    reserva=reserva,
                    agora=self.agora,
                )

        reserva.refresh_from_db()

        self.assertEqual(
            reserva.status,
            StatusReservaEstoque.ATIVA,
        )
        self.assertIsNone(reserva.expirada_em)

    def test_utiliza_estado_atual_do_banco(self):
        reserva = self.criar_reserva(
            expira_em=self.agora - timezone.timedelta(minutes=1)
        )

        reserva_desatualizada = ReservaEstoque.objects.get(
            pk=reserva.pk
        )

        ReservaEstoque.objects.filter(
            pk=reserva.pk
        ).update(
            status=StatusReservaEstoque.LIBERADA,
            liberada_em=self.agora,
        )

        with self.assertRaises(ValidationError):
            expirar_reserva_estoque(
                reserva=reserva_desatualizada,
                agora=self.agora,
            )
