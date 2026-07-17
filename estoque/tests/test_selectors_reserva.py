from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from core.choices import StatusOperacional
from empresas.models import Loja, Matriz
from estoque.choices import OrigemMovimentacao, StatusReservaEstoque
from estoque.models import ReservaEstoque, SaldoEstoque
from estoque.selectors import (
    get_quantidade_reservada,
    get_saldo_disponivel,
)
from produtos.models import Produto, UnidadeMedida


class SelectorsReservaEstoqueTestCase(TestCase):
    def setUp(self):
        self.matriz = Matriz.objects.create(
            nome='Matriz Selectors Reserva'
        )

        self.loja = Loja.objects.create(
            matriz=self.matriz,
            nome='Loja Selectors Reserva',
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
            codigo_interno='SEL-RES-001',
            nome='Produto Selectors Reserva',
            controla_estoque=True,
        )

        self.saldo = SaldoEstoque.objects.create(
            matriz=self.matriz,
            loja=self.loja,
            produto=self.produto,
            quantidade_atual=Decimal('10.000'),
        )

    def criar_reserva(
        self,
        *,
        quantidade,
        status=StatusReservaEstoque.ATIVA,
        chave,
    ):
        dados = {
            'matriz': self.matriz,
            'loja': self.loja,
            'produto': self.produto,
            'quantidade': Decimal(quantidade),
            'status': status,
            'origem': OrigemMovimentacao.VENDA,
            'chave_idempotencia': chave,
        }

        if status == StatusReservaEstoque.CONFIRMADA:
            dados['confirmada_em'] = timezone.now()

        if status == StatusReservaEstoque.LIBERADA:
            dados['liberada_em'] = timezone.now()

        if status == StatusReservaEstoque.CANCELADA:
            dados['cancelada_em'] = timezone.now()

        if status == StatusReservaEstoque.EXPIRADA:
            dados['expirada_em'] = timezone.now()

        return ReservaEstoque.objects.create(**dados)

    def test_quantidade_reservada_sem_reservas_retorna_zero(self):
        quantidade = get_quantidade_reservada(
            matriz=self.matriz,
            loja=self.loja,
            produto=self.produto,
        )

        self.assertEqual(
            quantidade,
            Decimal('0.000')
        )

    def test_quantidade_reservada_soma_apenas_reservas_ativas(self):
        self.criar_reserva(
            quantidade='2.000',
            chave='selector:ativa:001',
        )

        self.criar_reserva(
            quantidade='1.500',
            chave='selector:ativa:002',
        )

        self.criar_reserva(
            quantidade='3.000',
            status=StatusReservaEstoque.CONFIRMADA,
            chave='selector:confirmada:001',
        )

        self.criar_reserva(
            quantidade='4.000',
            status=StatusReservaEstoque.LIBERADA,
            chave='selector:liberada:001',
        )

        self.criar_reserva(
            quantidade='5.000',
            status=StatusReservaEstoque.CANCELADA,
            chave='selector:cancelada:001',
        )

        self.criar_reserva(
            quantidade='6.000',
            status=StatusReservaEstoque.EXPIRADA,
            chave='selector:expirada:001',
        )

        quantidade = get_quantidade_reservada(
            matriz=self.matriz,
            loja=self.loja,
            produto=self.produto,
        )

        self.assertEqual(
            quantidade,
            Decimal('3.500')
        )

    def test_quantidade_reservada_isola_loja(self):
        outra_loja = Loja.objects.create(
            matriz=self.matriz,
            nome='Outra Loja Selectors',
            status=StatusOperacional.ATIVA,
        )

        ReservaEstoque.objects.create(
            matriz=self.matriz,
            loja=outra_loja,
            produto=self.produto,
            quantidade=Decimal('7.000'),
            origem=OrigemMovimentacao.VENDA,
            chave_idempotencia='selector:outra-loja:001',
        )

        quantidade = get_quantidade_reservada(
            matriz=self.matriz,
            loja=self.loja,
            produto=self.produto,
        )

        self.assertEqual(
            quantidade,
            Decimal('0.000')
        )

    def test_quantidade_reservada_isola_produto(self):
        outro_produto = Produto.objects.create(
            matriz=self.matriz,
            unidade_medida=self.unidade,
            codigo_interno='SEL-RES-002',
            nome='Outro Produto Selectors',
            controla_estoque=True,
        )

        ReservaEstoque.objects.create(
            matriz=self.matriz,
            loja=self.loja,
            produto=outro_produto,
            quantidade=Decimal('7.000'),
            origem=OrigemMovimentacao.VENDA,
            chave_idempotencia='selector:outro-produto:001',
        )

        quantidade = get_quantidade_reservada(
            matriz=self.matriz,
            loja=self.loja,
            produto=self.produto,
        )

        self.assertEqual(
            quantidade,
            Decimal('0.000')
        )

    def test_quantidade_reservada_isola_matriz(self):
        outra_matriz = Matriz.objects.create(
            nome='Outra Matriz Selectors'
        )

        outra_loja = Loja.objects.create(
            matriz=outra_matriz,
            nome='Loja Outra Matriz Selectors',
            status=StatusOperacional.ATIVA,
        )

        outra_unidade = UnidadeMedida.objects.create(
            matriz=outra_matriz,
            sigla='UN',
            descricao='Unidade',
        )

        outro_produto = Produto.objects.create(
            matriz=outra_matriz,
            unidade_medida=outra_unidade,
            codigo_interno='SEL-RES-003',
            nome='Produto Outra Matriz',
            controla_estoque=True,
        )

        ReservaEstoque.objects.create(
            matriz=outra_matriz,
            loja=outra_loja,
            produto=outro_produto,
            quantidade=Decimal('7.000'),
            origem=OrigemMovimentacao.VENDA,
            chave_idempotencia='selector:outra-matriz:001',
        )

        quantidade = get_quantidade_reservada(
            matriz=self.matriz,
            loja=self.loja,
            produto=self.produto,
        )

        self.assertEqual(
            quantidade,
            Decimal('0.000')
        )

    def test_saldo_disponivel_sem_reservas_e_igual_ao_fisico(self):
        saldo_disponivel = get_saldo_disponivel(
            matriz=self.matriz,
            loja=self.loja,
            produto=self.produto,
        )

        self.assertEqual(
            saldo_disponivel,
            Decimal('10.000')
        )

    def test_saldo_disponivel_subtrai_reservas_ativas(self):
        self.criar_reserva(
            quantidade='2.500',
            chave='selector:saldo:001',
        )

        self.criar_reserva(
            quantidade='1.000',
            chave='selector:saldo:002',
        )

        saldo_disponivel = get_saldo_disponivel(
            matriz=self.matriz,
            loja=self.loja,
            produto=self.produto,
        )

        self.assertEqual(
            saldo_disponivel,
            Decimal('6.500')
        )

    def test_saldo_disponivel_ignora_reservas_encerradas(self):
        self.criar_reserva(
            quantidade='2.000',
            status=StatusReservaEstoque.CONFIRMADA,
            chave='selector:encerrada:001',
        )

        self.criar_reserva(
            quantidade='2.000',
            status=StatusReservaEstoque.LIBERADA,
            chave='selector:encerrada:002',
        )

        self.criar_reserva(
            quantidade='2.000',
            status=StatusReservaEstoque.CANCELADA,
            chave='selector:encerrada:003',
        )

        self.criar_reserva(
            quantidade='2.000',
            status=StatusReservaEstoque.EXPIRADA,
            chave='selector:encerrada:004',
        )

        saldo_disponivel = get_saldo_disponivel(
            matriz=self.matriz,
            loja=self.loja,
            produto=self.produto,
        )

        self.assertEqual(
            saldo_disponivel,
            Decimal('10.000')
        )

    def test_saldo_disponivel_sem_registro_de_saldo_retorna_zero(self):
        outro_produto = Produto.objects.create(
            matriz=self.matriz,
            unidade_medida=self.unidade,
            codigo_interno='SEL-RES-SEM-SALDO',
            nome='Produto sem saldo',
            controla_estoque=True,
        )

        saldo_disponivel = get_saldo_disponivel(
            matriz=self.matriz,
            loja=self.loja,
            produto=outro_produto,
        )

        self.assertEqual(
            saldo_disponivel,
            Decimal('0.000')
        )

    def test_saldo_disponivel_pode_expor_inconsistencia_negativa(self):
        self.criar_reserva(
            quantidade='12.000',
            chave='selector:inconsistencia:001',
        )

        saldo_disponivel = get_saldo_disponivel(
            matriz=self.matriz,
            loja=self.loja,
            produto=self.produto,
        )

        self.assertEqual(
            saldo_disponivel,
            Decimal('-2.000')
        )
