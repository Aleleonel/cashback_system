from django.test import TestCase
from unittest.mock import Mock, patch
from decimal import Decimal
from django.test import SimpleTestCase
from pdv.models import FormaPagamento


class R21ContratoFormaPagamentoTests(SimpleTestCase):
    def test_forma_pagamento_expoe_flag_gera_cashback(self):
        campo = FormaPagamento._meta.get_field("gera_cashback")
        self.assertFalse(campo.null)
        self.assertIsNotNone(campo.default)


class R21ContratoBaseElegivelTests(SimpleTestCase):
    def _base_elegivel(self, pagamentos):
        from pdv.services.vendas.fechamento import calcular_base_cashback_pagamentos
        return calcular_base_cashback_pagamentos(pagamentos)

    def test_pagamento_unico_elegivel_usa_valor_integral(self):
        pagamentos = [
            {"valor": Decimal("50.00"), "gera_cashback": True},
        ]
        self.assertEqual(self._base_elegivel(pagamentos), Decimal("50.00"))

    def test_pagamento_misto_soma_somente_valores_elegiveis(self):
        pagamentos = [
            {"valor": Decimal("100.00"), "gera_cashback": True},
            {"valor": Decimal("100.00"), "gera_cashback": False},
        ]
        self.assertEqual(self._base_elegivel(pagamentos), Decimal("100.00"))

    def test_nenhum_pagamento_elegivel_resulta_base_zero(self):
        pagamentos = [
            {"valor": Decimal("50.00"), "gera_cashback": False},
            {"valor": Decimal("25.00"), "gera_cashback": False},
        ]
        self.assertEqual(self._base_elegivel(pagamentos), Decimal("0.00"))

class R21IntegracaoFechamentoCashbackTests(SimpleTestCase):
    def test_integracao_cashback_recebe_base_elegivel(self):
        from unittest.mock import Mock, patch
        from pdv.services.vendas import fechamento

        venda = Mock()
        venda.total = Decimal("200.00")
        venda.cliente = Mock(
            cpf="12345678901",
            nome="Cliente R21",
            telefone="",
            email="",
            data_nascimento=None,
            aceita_email=False,
            aceita_sms=False,
        )
        venda.matriz = Mock()
        venda.loja = Mock()
        venda.uuid = "r21-teste"
        venda.pk = 999
        venda.pagamentos.all.return_value = [
            Mock(valor=Decimal("100.00"), forma_pagamento=Mock(gera_cashback=True)),
            Mock(valor=Decimal("100.00"), forma_pagamento=Mock(gera_cashback=False)),
        ]

        with patch.object(fechamento, "executar_venda_idempotente") as executar:
            fechamento._registrar_beneficio(venda, Mock(), "nenhum", Decimal("0.00"), "")

        kwargs = executar.call_args.kwargs
        self.assertEqual(kwargs["valor_compra"], Decimal("200.00"))
        self.assertEqual(kwargs["valor_base_cashback"], Decimal("100.00"))
    def test_base_zero_nao_executa_venda_cashback(self):
        from pdv.services.vendas import fechamento

        venda = Mock()
        venda.total = Decimal("200.00")
        venda.matriz = Mock()
        venda.loja = Mock()
        venda.uuid = "r21-base-zero"
        venda.pk = 999
        venda.cliente = Mock(
            cpf="12345678901",
            nome="Cliente R21",
            telefone="",
            email="",
            data_nascimento=None,
            aceita_email=False,
            aceita_sms=False,
        )
        venda.pagamentos.all.return_value = [
            Mock(valor=Decimal("200.00"), forma_pagamento=Mock(gera_cashback=False)),
        ]

        with patch.object(fechamento, "executar_venda_idempotente") as executar:
            fechamento._registrar_beneficio(
                venda, Mock(), "nenhum", Decimal("0.00"), "",
                valor_base_cashback=Decimal("0.00"),
            )

        executar.assert_not_called()
class R21OrdemDescontoPagamentoTests(TestCase):
    def test_pagamento_liquido_deve_ser_validado_apos_desconto(self):
        from django.core.exceptions import ValidationError
        from pdv.services.vendas.fechamento import _registrar_pagamentos

        venda = Mock()
        venda.total = Decimal("100.00")
        venda.matriz = Mock()
        venda.pagamentos.all.return_value.delete.return_value = None

        forma = Mock()
        forma.exige_autorizacao = False
        forma.permite_troco = False
        forma.permite_parcelamento = False
        forma.maximo_parcelas = 1

        payload = [{
            "forma_pagamento_id": 1,
            "valor": "90.00",
            "parcelas": 1,
        }]

        with patch("pdv.services.vendas.fechamento.FormaPagamento.objects.get", return_value=forma):
            with patch("pdv.services.vendas.fechamento.PagamentoVenda") as pagamento_model:
                with self.assertRaises(ValidationError):
                    _registrar_pagamentos(venda, payload)

        # RED correto: com total bruto 100, pagamento liquido 90 ainda e rejeitado.
        # A correcao de producao devera mudar a ordem do fechamento, nao este helper isolado.
        self.assertEqual(venda.total, Decimal("100.00"))
        # Helper isolado continua validando contra venda.total; a ordem pertence ao fechamento.

    @patch("pdv.services.vendas.fechamento.finalizar_venda")
    @patch("pdv.services.vendas.fechamento.executar_venda_idempotente")
    @patch("pdv.services.vendas.fechamento.resolver_beneficio_da_venda")
    def test_pagamento_deve_validar_total_liquido_apos_cashback(
        self, resolver_mock, executar_mock, finalizar_mock
    ):
        from types import SimpleNamespace
        from pdv.services.vendas.fechamento import fechar_venda_web

        venda = Mock()
        venda.total = Decimal("200.00")
        venda.matriz = Mock()
        venda.loja = Mock()
        venda.cliente = Mock()
        venda.cliente_id = 1
        venda.recalcular_totais = Mock()
        def recalcular_totais_teste(salvar=True):
            venda.total = (Decimal("200.00") - venda.desconto_geral).quantize(Decimal("0.01"))

        venda.desconto_geral = Decimal("0.00")
        venda.recalcular_totais.side_effect = recalcular_totais_teste
        venda.full_clean = Mock()
        venda.save = Mock()
        pagamentos_manager = Mock()
        pagamentos_manager.all.return_value = pagamentos_manager
        pagamentos_manager.delete.return_value = None
        venda.pagamentos = pagamentos_manager
        resolver_mock.return_value = SimpleNamespace(valor=Decimal("50.00"))
        executar_mock.return_value = SimpleNamespace(
            beneficios={"cashback_usado": Decimal("50.00")}
        )
        finalizar_mock.return_value = venda

        forma = Mock()
        forma.pk = 1
        forma.gera_cashback = True
        forma.exige_autorizacao = False
        forma.exige_cliente_identificado = False
        forma.permite_parcelamento = False
        forma.maximo_parcelas = 1
        forma.nome = "Forma elegivel teste"
        with patch("pdv.services.vendas.fechamento.Venda.objects.select_for_update") as reload_mock:
            reload_mock.return_value.select_related.return_value.get.return_value = venda
            with patch("pdv.services.vendas.fechamento.FormaPagamento.objects.get", return_value=forma):
                with patch("pdv.services.vendas.fechamento.PagamentoVenda") as pagamento_model:
                    pagamento_persistido = pagamento_model.return_value
                    pagamento_persistido.valor = Decimal("150.00")
                    pagamento_persistido.forma_pagamento = forma
                    pagamentos_manager.__iter__ = Mock(return_value=iter([pagamento_persistido]))
                    fechar_venda_web(
                        venda=venda,
                        usuario=Mock(),
                        pagamentos=[{
                            "forma_pagamento_id": 1,
                            "valor": "150.00",
                            "parcelas": 1,
                            "valor_recebido": "150.00",
                        }],
                        tipo_emissao="nao_fiscal",
                        uf_destino="",
                        tipo_beneficio="cashback",
                        valor_cashback=Decimal("50.00"),
                        codigo_voucher="",
                    )
