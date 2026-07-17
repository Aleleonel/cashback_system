from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone

from core.choices import StatusOperacional
from empresas.models import Loja, Matriz
from estoque.choices import OrigemMovimentacao, StatusReservaEstoque
from estoque.models import ReservaEstoque
from produtos.models import Produto, UnidadeMedida


class ReservaEstoqueModelTestCase(TestCase):
    def setUp(self):
        self.matriz = Matriz.objects.create(
            nome='Matriz Reserva'
        )

        self.loja = Loja.objects.create(
            matriz=self.matriz,
            nome='Loja Reserva',
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
            codigo_interno='RES-001',
            nome='Produto Reserva',
            controla_estoque=True,
        )

    def criar_reserva(self, **dados):
        padrao = {
            'matriz': self.matriz,
            'loja': self.loja,
            'produto': self.produto,
            'quantidade': Decimal('3.000'),
            'status': StatusReservaEstoque.ATIVA,
            'origem': OrigemMovimentacao.VENDA,
            'chave_idempotencia': 'reserva:teste:001',
        }

        padrao.update(dados)

        return ReservaEstoque.objects.create(**padrao)

    def test_cria_reserva_ativa_valida(self):
        reserva = self.criar_reserva()

        self.assertIsNotNone(reserva.uuid)
        self.assertEqual(
            reserva.status,
            StatusReservaEstoque.ATIVA
        )
        self.assertEqual(
            reserva.quantidade,
            Decimal('3.000')
        )
        self.assertIsNotNone(reserva.criado_em)
        self.assertIsNotNone(reserva.atualizado_em)

    def test_status_padrao_e_ativo(self):
        reserva = self.criar_reserva(
            status=StatusReservaEstoque.ATIVA
        )

        self.assertEqual(
            reserva.status,
            StatusReservaEstoque.ATIVA
        )

    def test_rejeita_quantidade_zero(self):
        with self.assertRaises(ValidationError):
            self.criar_reserva(
                quantidade=Decimal('0.000')
            )

    def test_rejeita_quantidade_negativa(self):
        with self.assertRaises(ValidationError):
            self.criar_reserva(
                quantidade=Decimal('-1.000')
            )

    def test_rejeita_loja_de_outra_matriz(self):
        outra_matriz = Matriz.objects.create(
            nome='Outra Matriz Reserva'
        )

        outra_loja = Loja.objects.create(
            matriz=outra_matriz,
            nome='Outra Loja Reserva',
            status=StatusOperacional.ATIVA,
        )

        with self.assertRaises(ValidationError):
            self.criar_reserva(
                loja=outra_loja
            )

    def test_rejeita_produto_de_outra_matriz(self):
        outra_matriz = Matriz.objects.create(
            nome='Matriz Outro Produto Reserva'
        )

        outra_unidade = UnidadeMedida.objects.create(
            matriz=outra_matriz,
            sigla='CX',
            descricao='Caixa',
        )

        outro_produto = Produto.objects.create(
            matriz=outra_matriz,
            unidade_medida=outra_unidade,
            codigo_interno='RES-OUT-001',
            nome='Outro Produto Reserva',
            controla_estoque=True,
        )

        with self.assertRaises(ValidationError):
            self.criar_reserva(
                produto=outro_produto
            )

    def test_rejeita_produto_sem_controle_de_estoque(self):
        produto = Produto.objects.create(
            matriz=self.matriz,
            unidade_medida=self.unidade,
            codigo_interno='RES-SEM-001',
            nome='Produto sem estoque',
            controla_estoque=False,
        )

        with self.assertRaises(ValidationError):
            self.criar_reserva(
                produto=produto
            )

    def test_chave_idempotencia_e_unica_por_matriz(self):
        self.criar_reserva()

        with self.assertRaises(ValidationError):
            self.criar_reserva()

    def test_constraint_de_idempotencia_protege_o_banco(self):
        self.criar_reserva()

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                ReservaEstoque.objects.bulk_create([
                    ReservaEstoque(
                        matriz=self.matriz,
                        loja=self.loja,
                        produto=self.produto,
                        quantidade=Decimal('1.000'),
                        origem=OrigemMovimentacao.VENDA,
                        chave_idempotencia='reserva:teste:001',
                    )
                ])

    def test_chave_vazia_pode_se_repetir(self):
        self.criar_reserva(
            chave_idempotencia=''
        )

        segunda = self.criar_reserva(
            chave_idempotencia=''
        )

        self.assertIsNotNone(segunda.pk)

    def test_mesma_chave_pode_existir_em_outra_matriz(self):
        self.criar_reserva()

        outra_matriz = Matriz.objects.create(
            nome='Segunda Matriz Reserva'
        )

        outra_loja = Loja.objects.create(
            matriz=outra_matriz,
            nome='Segunda Loja Reserva',
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
            codigo_interno='RES-002',
            nome='Segundo Produto Reserva',
            controla_estoque=True,
        )

        reserva = ReservaEstoque.objects.create(
            matriz=outra_matriz,
            loja=outra_loja,
            produto=outro_produto,
            quantidade=Decimal('1.000'),
            origem=OrigemMovimentacao.VENDA,
            chave_idempotencia='reserva:teste:001',
        )

        self.assertIsNotNone(reserva.pk)

    def test_normaliza_campos_textuais(self):
        reserva = self.criar_reserva(
            origem_id='  item-venda-1  ',
            chave_idempotencia='  reserva:teste:002  ',
            documento_referencia='  VENDA-123  ',
        )

        self.assertEqual(
            reserva.origem_id,
            'item-venda-1'
        )
        self.assertEqual(
            reserva.chave_idempotencia,
            'reserva:teste:002'
        )
        self.assertEqual(
            reserva.documento_referencia,
            'VENDA-123'
        )

    def test_reserva_ativa_rejeita_data_de_encerramento(self):
        with self.assertRaises(ValidationError):
            self.criar_reserva(
                confirmada_em=timezone.now()
            )

    def test_confirmada_exige_confirmada_em(self):
        with self.assertRaises(ValidationError) as contexto:
            self.criar_reserva(
                status=StatusReservaEstoque.CONFIRMADA
            )

        self.assertIn(
            'confirmada_em',
            contexto.exception.message_dict
        )

    def test_confirmada_valida_com_data_correspondente(self):
        reserva = self.criar_reserva(
            status=StatusReservaEstoque.CONFIRMADA,
            confirmada_em=timezone.now(),
        )

        self.assertEqual(
            reserva.status,
            StatusReservaEstoque.CONFIRMADA
        )

    def test_liberada_exige_liberada_em(self):
        with self.assertRaises(ValidationError) as contexto:
            self.criar_reserva(
                status=StatusReservaEstoque.LIBERADA
            )

        self.assertIn(
            'liberada_em',
            contexto.exception.message_dict
        )

    def test_cancelada_exige_cancelada_em(self):
        with self.assertRaises(ValidationError) as contexto:
            self.criar_reserva(
                status=StatusReservaEstoque.CANCELADA
            )

        self.assertIn(
            'cancelada_em',
            contexto.exception.message_dict
        )

    def test_expirada_exige_expirada_em(self):
        with self.assertRaises(ValidationError) as contexto:
            self.criar_reserva(
                status=StatusReservaEstoque.EXPIRADA
            )

        self.assertIn(
            'expirada_em',
            contexto.exception.message_dict
        )

    def test_rejeita_datas_incompativeis_com_status(self):
        with self.assertRaises(ValidationError) as contexto:
            self.criar_reserva(
                status=StatusReservaEstoque.CONFIRMADA,
                confirmada_em=timezone.now(),
                cancelada_em=timezone.now(),
            )

        self.assertIn(
            'status',
            contexto.exception.message_dict
        )

    def test_string_da_reserva_e_legivel(self):
        reserva = self.criar_reserva()

        texto = str(reserva)

        self.assertIn(
            self.produto.codigo_interno,
            texto
        )
        self.assertIn(
            self.loja.nome,
            texto
        )
        self.assertIn(
            'Ativa',
            texto
        )
