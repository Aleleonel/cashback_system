from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from clientes.models import Cliente
from empresas.models import Loja, Matriz
from pdv.models import Venda
from pdv.services.vendas.beneficios import BeneficioResolvido
from pdv.services.vendas.fechamento import _registrar_beneficio


class FechamentoUsaAdapterBeneficiosTests(TestCase):
    def setUp(self):
        self.matriz = Matriz.objects.create(nome="Matriz Integracao Adapter")
        self.loja = Loja.objects.create(
            matriz=self.matriz,
            nome="Loja Integracao Adapter",
        )
        self.usuario = get_user_model().objects.create_user(
            username="usuario_integracao_adapter",
            password="senha-teste",
            matriz=self.matriz,
        )
        self.usuario.lojas.add(self.loja)
        self.cliente = Cliente.objects.create(
            matriz=self.matriz,
            loja_cadastro=self.loja,
            nome="Cliente Integracao Adapter",
            cpf="74185296300",
        )
        self.venda = Venda.objects.create(
            matriz=self.matriz,
            loja=self.loja,
            operador=self.usuario,
            cliente=self.cliente,
            subtotal=Decimal("100.00"),
            total=Decimal("100.00"),
        )

    @patch("pdv.services.vendas.fechamento.executar_venda_idempotente")
    @patch("pdv.services.vendas.fechamento.resolver_beneficio_da_venda")
    def test_fechamento_consulta_adapter_antes_da_persistencia(
        self,
        resolver_mock,
        executar_mock,
    ):
        resolver_mock.return_value = BeneficioResolvido(
            tipo="voucher",
            valor=Decimal("10.00"),
            voucher=object(),
            codigo="TESTE10",
        )
        executar_mock.return_value.beneficios = {
            "desconto_voucher": Decimal("10.00"),
            "cashback_usado": Decimal("0.00"),
        }

        desconto = _registrar_beneficio(
            self.venda,
            self.usuario,
            "voucher",
            Decimal("0.00"),
            "TESTE10",
        )

        self.assertEqual(desconto, Decimal("10.00"))
        resolver_mock.assert_called_once_with(
            matriz=self.matriz,
            loja=self.loja,
            cliente=self.cliente,
            valor_compra=Decimal("100.00"),
            tipo_beneficio="voucher",
            valor_cashback=Decimal("0.00"),
            codigo_voucher="TESTE10",
        )
        executar_mock.assert_called_once()

    @patch("pdv.services.vendas.fechamento.executar_venda_idempotente")
    @patch("pdv.services.vendas.fechamento.resolver_beneficio_da_venda")
    def test_divergencia_entre_adapter_e_persistencia_e_bloqueada(
        self,
        resolver_mock,
        executar_mock,
    ):
        resolver_mock.return_value = BeneficioResolvido(
            tipo="voucher",
            valor=Decimal("10.00"),
            voucher=object(),
            codigo="TESTE10",
        )
        executar_mock.return_value.beneficios = {
            "desconto_voucher": Decimal("8.00"),
            "cashback_usado": Decimal("0.00"),
        }

        with self.assertRaisesMessage(
            ValidationError,
            "adaptador=10.00"        ):
            _registrar_beneficio(
                self.venda,
                self.usuario,
                "voucher",
                Decimal("0.00"),
                "TESTE10",
            )
