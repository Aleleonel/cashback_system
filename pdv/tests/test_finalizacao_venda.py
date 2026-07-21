from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from empresas.models import Loja, Matriz
from pdv.choices import StatusOperacaoVenda
from pdv.models import Caixa, SessaoCaixa, Venda
from pdv.services.vendas.finalizacao import finalizar_venda


class FinalizacaoVendaOrquestradorTests(TestCase):
    def setUp(self):
        self.matriz = Matriz.objects.create(nome="Matriz Finalizacao")
        self.loja = Loja.objects.create(
            matriz=self.matriz,
            nome="Loja Finalizacao",
            cnpj="11.111.111/0001-11",
        )
        self.usuario = get_user_model().objects.create_user(
            username="operador_finalizacao",
            password="senha-teste",
            matriz=self.matriz,
        )
        self.usuario.lojas.add(self.loja)

        self.caixa = Caixa.objects.create(
            matriz=self.matriz,
            loja=self.loja,
            nome="Caixa Finalizacao",
            codigo="CX-FIN",
        )
        self.sessao = SessaoCaixa.objects.create(
            caixa=self.caixa,
            operador_abertura=self.usuario,
            valor_abertura=Decimal("0.00"),
        )
        self.venda = Venda.objects.create(
            matriz=self.matriz,
            loja=self.loja,
            sessao_caixa=self.sessao,
            operador=self.usuario,
            vendedor=self.usuario,
            status=StatusOperacaoVenda.ABERTA,
            subtotal=Decimal("10.00"),
            desconto=Decimal("0.00"),
            acrescimo=Decimal("0.00"),
            total=Decimal("10.00"),
        )

    @patch("pdv.services.vendas.finalizacao.registrar_auditoria_finalizacao_venda")
    @patch("pdv.services.vendas.finalizacao.registrar_movimentacao_caixa_venda")
    @patch("pdv.services.vendas.finalizacao._confirmar_reservas")
    @patch("pdv.services.vendas.finalizacao.validar_venda_para_finalizacao")
    def test_finaliza_venda_em_transacao_unica(
        self,
        validar_mock,
        confirmar_mock,
        caixa_mock,
        auditoria_mock,
    ):
        resultado = finalizar_venda(
            venda=self.venda,
            usuario=self.usuario,
        )

        resultado.refresh_from_db()
        self.assertEqual(
            resultado.status,
            StatusOperacaoVenda.FINALIZADA,
        )
        self.assertIsNotNone(resultado.finalizada_em)
        validar_mock.assert_called_once()
        confirmar_mock.assert_called_once()
        caixa_mock.assert_called_once()
        auditoria_mock.assert_called_once()

    @patch("pdv.services.vendas.finalizacao.registrar_movimentacao_caixa_venda")
    @patch("pdv.services.vendas.finalizacao._confirmar_reservas")
    @patch("pdv.services.vendas.finalizacao.validar_venda_para_finalizacao")
    def test_rollback_quando_caixa_falha(
        self,
        validar_mock,
        confirmar_mock,
        caixa_mock,
    ):
        def alterar_temporariamente(**kwargs):
            Venda.objects.filter(pk=self.venda.pk).update(
                observacao="alteracao temporaria"
            )
            return []

        confirmar_mock.side_effect = alterar_temporariamente
        caixa_mock.side_effect = RuntimeError("falha simulada no caixa")

        with self.assertRaises(RuntimeError):
            finalizar_venda(
                venda=self.venda,
                usuario=self.usuario,
            )

        self.venda.refresh_from_db()
        self.assertEqual(
            self.venda.status,
            StatusOperacaoVenda.ABERTA,
        )
        self.assertEqual(self.venda.observacao, "")

    @patch("pdv.services.vendas.finalizacao.registrar_auditoria_finalizacao_venda")
    @patch("pdv.services.vendas.finalizacao.registrar_movimentacao_caixa_venda")
    @patch("pdv.services.vendas.finalizacao._confirmar_reservas")
    @patch("pdv.services.vendas.finalizacao.validar_venda_para_finalizacao")
    def test_reprocessamento_de_venda_finalizada_e_idempotente(
        self,
        validar_mock,
        confirmar_mock,
        caixa_mock,
        auditoria_mock,
    ):
        self.venda.status = StatusOperacaoVenda.FINALIZADA
        self.venda.finalizada_em = timezone.now()
        self.venda.save(update_fields=["status", "finalizada_em"])

        resultado = finalizar_venda(
            venda=self.venda,
            usuario=self.usuario,
        )

        self.assertEqual(resultado.pk, self.venda.pk)
        validar_mock.assert_not_called()
        confirmar_mock.assert_not_called()
        caixa_mock.assert_not_called()
        auditoria_mock.assert_not_called()
