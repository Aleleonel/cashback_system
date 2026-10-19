from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.test import SimpleTestCase

from pdv.models import ItemVenda


class F25CCMVHistoricoContratoRedTests(SimpleTestCase):
    """
    F25C - contrato estrutural do CMV historico.

    Premissas:
    - o banco atual e de teste/desenvolvimento;
    - nao existe obrigacao de preservar vendas antigas;
    - o contrato deve nascer correto para a futura producao;
    - o CMV de uma venda finalizada nao pode depender do custo atual
      do cadastro do produto;
    - o snapshot economico deve ser congelado na finalizacao.
    """

    def test_item_venda_possui_custo_unitario_snapshot(self):
        campo = ItemVenda._meta.get_field("custo_unitario_snapshot")

        self.assertIsInstance(campo, models.DecimalField)
        self.assertEqual(campo.max_digits, 14)
        self.assertEqual(campo.decimal_places, 2)

    def test_custo_unitario_snapshot_nao_aceita_null(self):
        campo = ItemVenda._meta.get_field("custo_unitario_snapshot")

        self.assertFalse(
            campo.null,
            "Novo contrato deve exigir custo unitario conhecido.",
        )

    def test_custo_unitario_snapshot_tem_default_zero(self):
        campo = ItemVenda._meta.get_field("custo_unitario_snapshot")

        self.assertEqual(
            campo.get_default(),
            Decimal("0.00"),
            "Produto com custo_base zero deve continuar representando custo zero.",
        )

    def test_custo_unitario_snapshot_nao_pode_ser_negativo(self):
        campo = ItemVenda._meta.get_field("custo_unitario_snapshot")
        limites = [
            getattr(validator, "limit_value", None)
            for validator in campo.validators
            if isinstance(validator, MinValueValidator)
        ]

        self.assertIn(Decimal("0.00"), limites)

    def test_item_venda_expoe_custo_total_snapshot(self):
        self.assertTrue(
            hasattr(ItemVenda, "custo_total_snapshot"),
            "ItemVenda deve expor custo_total_snapshot.",
        )

    def test_custo_total_snapshot_e_derivado_e_nao_campo_persistido(self):
        nomes_campos = {
            campo.name
            for campo in ItemVenda._meta.get_fields()
        }

        self.assertNotIn(
            "custo_total_snapshot",
            nomes_campos,
            "Evitar duplicar dado derivavel: total deve vir de quantidade x custo unitario.",
        )

    def test_custo_total_snapshot_mantem_precisao_monetaria(self):
        """
        Congela a regra matematica esperada sem depender de fixtures.
        O teste passara quando a propriedade existir no modelo.
        """
        item = ItemVenda(
            quantidade=Decimal("2.500"),
            custo_unitario_snapshot=Decimal("12.34"),
        )

        self.assertEqual(
            item.custo_total_snapshot,
            Decimal("30.85"),
        )