from decimal import Decimal

from unittest.mock import patch



from django.core.exceptions import ValidationError

from django.test import TestCase

from django.utils import timezone



from auditoria.models import RegistroAuditoria

from core.choices import StatusOperacional

from empresas.models import Loja, Matriz

from estoque.choices import (

    NaturezaMovimentacao,

    OrigemMovimentacao,

    StatusReservaEstoque,

    TipoMovimentacao,

)

from estoque.models import (

    MovimentacaoEstoque,

    ReservaEstoque,

    SaldoEstoque,

)

from estoque.selectors import get_saldo_disponivel

from estoque.services import confirmar_reserva_estoque

from produtos.models import Produto, UnidadeMedida





class ConfirmarReservaEstoqueTestCase(TestCase):

    def setUp(self):

        self.matriz = Matriz.objects.create(

            nome='Matriz Confirmação Reserva'

        )



        self.loja = Loja.objects.create(

            matriz=self.matriz,

            nome='Loja Confirmação Reserva',

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

            codigo_interno='CONF-RES-001',

            nome='Produto Confirmação Reserva',

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

            origem_id='item-venda-001',

            chave_idempotencia='reserva:venda:001',

            documento_referencia='VENDA-001',

        )



    def confirmar(self, **dados):

        padrao = {

            'reserva': self.reserva,

        }



        padrao.update(dados)



        return confirmar_reserva_estoque(**padrao)



    def test_confirma_reserva_e_cria_saida_de_venda(self):

        resultado = self.confirmar()



        self.assertFalse(resultado.duplicada)

        self.assertEqual(

            resultado.reserva.status,

            StatusReservaEstoque.CONFIRMADA,

        )

        self.assertIsNotNone(

            resultado.reserva.confirmada_em

        )

        self.assertEqual(

            resultado.movimentacao.tipo,

            TipoMovimentacao.VENDA,

        )

        self.assertEqual(

            resultado.movimentacao.natureza,

            NaturezaMovimentacao.SAIDA,

        )

        self.assertEqual(

            resultado.movimentacao.origem,

            OrigemMovimentacao.VENDA,

        )

        self.assertEqual(

            resultado.movimentacao.quantidade,

            Decimal('4.000'),

        )



    def test_reduz_saldo_fisico_sem_reduzir_disponivel_duas_vezes(self):

        self.assertEqual(

            get_saldo_disponivel(

                matriz=self.matriz,

                loja=self.loja,

                produto=self.produto,

            ),

            Decimal('6.000'),

        )



        resultado = self.confirmar()



        self.assertEqual(

            resultado.saldo.quantidade_atual,

            Decimal('6.000'),

        )

        self.assertEqual(

            get_saldo_disponivel(

                matriz=self.matriz,

                loja=self.loja,

                produto=self.produto,

            ),

            Decimal('6.000'),

        )



    def test_propaga_referencias_da_reserva(self):

        resultado = self.confirmar()



        self.assertEqual(

            resultado.movimentacao.documento_referencia,

            'VENDA-001',

        )

        self.assertEqual(

            resultado.movimentacao.origem_id,

            'item-venda-001',

        )

        self.assertEqual(

            resultado.movimentacao.chave_idempotencia,

            'reserva:venda:001:confirmacao',

        )

        self.assertIn(

            str(self.reserva.uuid),

            resultado.movimentacao.observacao,

        )



    def test_confirmacao_repetida_e_idempotente(self):

        primeiro = self.confirmar()

        segundo = self.confirmar()



        self.assertFalse(primeiro.duplicada)

        self.assertTrue(segundo.duplicada)

        self.assertEqual(

            primeiro.movimentacao.pk,

            segundo.movimentacao.pk,

        )

        self.assertEqual(

            MovimentacaoEstoque.objects.count(),

            1,

        )



    def test_confirmacao_repetida_preserva_timestamp(self):

        primeiro = self.confirmar()

        confirmada_em = primeiro.reserva.confirmada_em



        segundo = self.confirmar()



        self.assertEqual(

            segundo.reserva.confirmada_em,

            confirmada_em,

        )



    def test_confirmacao_repetida_nao_duplica_auditoria_da_reserva(self):

        self.confirmar()

        self.confirmar()



        self.assertEqual(

            RegistroAuditoria.objects.filter(

                recurso='estoque.reserva',

                recurso_id=str(self.reserva.uuid),

                acao=RegistroAuditoria.ACAO_EDITAR,

            ).count(),

            1,

        )



    def test_registra_auditoria_da_confirmacao(self):

        resultado = self.confirmar()



        auditoria = RegistroAuditoria.objects.get(

            recurso='estoque.reserva',

            recurso_id=str(resultado.reserva.uuid),

            acao=RegistroAuditoria.ACAO_EDITAR,

        )



        self.assertIn(

            'Confirmação de reserva de estoque',

            auditoria.descricao,

        )

        self.assertIn(

            str(resultado.movimentacao.uuid),

            auditoria.descricao,

        )

        self.assertIn(

            'saldo_anterior=10.000',

            auditoria.descricao,

        )

        self.assertIn(

            'saldo_posterior=6.000',

            auditoria.descricao,

        )



    def test_falha_na_auditoria_desfaz_saida_e_confirmacao(self):

        with patch(

            'estoque.services.movimentacoes.confirmacoes.'

            'registrar_auditoria',

            side_effect=RuntimeError('Falha simulada de auditoria'),

        ):

            with self.assertRaises(RuntimeError):

                self.confirmar()



        self.reserva.refresh_from_db()

        self.saldo.refresh_from_db()



        self.assertEqual(

            self.reserva.status,

            StatusReservaEstoque.ATIVA,

        )

        self.assertIsNone(

            self.reserva.confirmada_em

        )

        self.assertEqual(

            self.saldo.quantidade_atual,

            Decimal('10.000'),

        )

        self.assertFalse(

            MovimentacaoEstoque.objects.exists()

        )

        self.assertFalse(

            RegistroAuditoria.objects.exists()

        )



    def test_rejeita_reserva_liberada_cancelada_ou_expirada(self):

        casos = (

            (StatusReservaEstoque.LIBERADA, 'liberada_em'),

            (StatusReservaEstoque.CANCELADA, 'cancelada_em'),

            (StatusReservaEstoque.EXPIRADA, 'expirada_em'),

        )



        for status, campo_timestamp in casos:

            with self.subTest(status=status):

                reserva = ReservaEstoque.objects.create(

                    matriz=self.matriz,

                    loja=self.loja,

                    produto=self.produto,

                    quantidade=Decimal('1.000'),

                    origem=OrigemMovimentacao.VENDA,

                    chave_idempotencia=(

                        f'reserva:estado:{status}'

                    ),

                    status=status,

                    **{

                        campo_timestamp: timezone.now(),

                    },

                )



                with self.assertRaises(ValidationError):

                    confirmar_reserva_estoque(

                        reserva=reserva

                    )



    def test_rejeita_reserva_de_origem_nao_venda(self):

        reserva = ReservaEstoque.objects.create(

            matriz=self.matriz,

            loja=self.loja,

            produto=self.produto,

            quantidade=Decimal('1.000'),

            origem=OrigemMovimentacao.SISTEMA,

            chave_idempotencia='reserva:sistema:001',

        )



        with self.assertRaises(ValidationError) as contexto:

            confirmar_reserva_estoque(

                reserva=reserva

            )



        self.assertIn(

            'origem',

            contexto.exception.message_dict,

        )



    def test_utiliza_estado_atual_do_banco(self):

        outra_instancia = ReservaEstoque.objects.get(

            pk=self.reserva.pk

        )



        primeiro = confirmar_reserva_estoque(

            reserva=outra_instancia

        )

        segundo = confirmar_reserva_estoque(

            reserva=self.reserva

        )



        self.assertFalse(primeiro.duplicada)

        self.assertTrue(segundo.duplicada)



    def test_rejeita_reserva_ativa_vencida(self):

        reserva = self.reserva



        ReservaEstoque.objects.filter(

            pk=reserva.pk

        ).update(

            expira_em=(

                timezone.now()

                - timezone.timedelta(minutes=1)

            )

        )



        reserva.refresh_from_db()



        with self.assertRaises(ValidationError) as contexto:

            confirmar_reserva_estoque(

                reserva=reserva,

            )



        self.assertIn(

            'expira_em',

            contexto.exception.message_dict,

        )



        reserva.refresh_from_db()

        self.saldo.refresh_from_db()



        self.assertEqual(

            reserva.status,

            StatusReservaEstoque.ATIVA,

        )

        self.assertEqual(

            self.saldo.quantidade_atual,

            Decimal('10.000'),

        )
