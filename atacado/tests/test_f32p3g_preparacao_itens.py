from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import Mock
from django.core.exceptions import ValidationError
from django.test import SimpleTestCase
from atacado.integracao_itens_pdv import preparar_itens_pdv


def pedido(itens, total):
    qs = Mock()
    qs.all.return_value.order_by.return_value = itens
    return SimpleNamespace(itens=qs, total=total)


def item(q="2.000", preco="10.00", produto=1):
    return SimpleNamespace(quantidade=q, preco_unitario_final=preco, produto_id=produto)


class PreparacaoItensPDVTests(SimpleTestCase):
    def test_total_exato(self):
        itens, t = preparar_itens_pdv(pedido=pedido([item()], "20.00"))
        self.assertEqual(t["total"], Decimal("20.00"))
        self.assertEqual(itens[0]["sequencia"], 1)

    def test_frete_ou_acrescimo(self):
        _, t = preparar_itens_pdv(pedido=pedido([item()], "23.50"))
        self.assertEqual(t["acrescimo_geral"], Decimal("3.50"))

    def test_desconto(self):
        _, t = preparar_itens_pdv(pedido=pedido([item()], "18.00"))
        self.assertEqual(t["desconto_geral"], Decimal("2.00"))

    def test_sem_itens(self):
        with self.assertRaises(ValidationError): preparar_itens_pdv(pedido=pedido([], "0.00"))

    def test_quantidade_invalida(self):
        with self.assertRaises(ValidationError): preparar_itens_pdv(pedido=pedido([item(q="0")], "0.00"))

    def test_preco_invalido(self):
        with self.assertRaises(ValidationError): preparar_itens_pdv(pedido=pedido([item(preco="NaN")], "20.00"))
