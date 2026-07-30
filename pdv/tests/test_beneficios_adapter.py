from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from clientes.models import Cliente
from core.models import ConfiguracaoSistema
from empresas.models import Loja, Matriz
from pdv.models import Venda
from pdv.services.vendas.beneficios import (
    BeneficioResolvido,
    registrar_voucher_da_venda,
    resolver_beneficio_da_venda,
)
from vouchers.models import Voucher


class BeneficiosPdvAdapterTests(TestCase):
    def setUp(self):
        self.matriz = Matriz.objects.create(nome="Matriz Adapter")
        self.loja = Loja.objects.create(
            matriz=self.matriz,
            nome="Loja Adapter",
        )
        self.cliente = Cliente.objects.create(
            matriz=self.matriz,
            loja_cadastro=self.loja,
            nome="Cliente Adapter",
            cpf="32165498700",
        )
        self.usuario = get_user_model().objects.create_user(
            username="usuario_adapter",
            password="senha-teste",
            matriz=self.matriz,
        )
        self.usuario.lojas.add(self.loja)
        self.configuracao = ConfiguracaoSistema.objects.create(
            matriz=self.matriz,
            percentual_cashback=Decimal("5.00"),
            valor_minimo_compra=Decimal("0.00"),
            percentual_maximo_beneficio=Decimal("30.00"),
        )
        hoje = timezone.localdate()
        self.voucher = Voucher.objects.create(
            matriz=self.matriz,
            codigo="ADAPTER10",
            nome="Voucher Adapter",
            tipo=Voucher.Tipo.PERCENTUAL,
            percentual=Decimal("10.00"),
            data_inicio=hoje,
            data_fim=hoje + timedelta(days=30),
            limite_utilizacao=2,
            uso_unico_por_cliente=False,
        )

    def test_resolve_nenhum_sem_persistir(self):
        beneficio = resolver_beneficio_da_venda(
            matriz=self.matriz,
            loja=self.loja,
            valor_compra=Decimal("100.00"),
            tipo_beneficio="nenhum",
        )

        self.assertEqual(beneficio, BeneficioResolvido.nenhum())
        self.voucher.refresh_from_db()
        self.assertEqual(self.voucher.total_utilizado, 0)
        self.assertEqual(self.voucher.usos.count(), 0)

    def test_resolve_voucher_reutilizando_calculo_central(self):
        beneficio = resolver_beneficio_da_venda(
            matriz=self.matriz,
            loja=self.loja,
            valor_compra=Decimal("100.00"),
            tipo_beneficio="voucher",
            codigo_voucher="adapter10",
        )

        self.assertEqual(beneficio.tipo, "voucher")
        self.assertEqual(beneficio.valor, Decimal("10.00"))
        self.assertEqual(beneficio.voucher, self.voucher)
        self.assertEqual(beneficio.codigo, "ADAPTER10")

    def test_resolver_voucher_nao_registra_uso(self):
        resolver_beneficio_da_venda(
            matriz=self.matriz,
            loja=self.loja,
            valor_compra=Decimal("100.00"),
            tipo_beneficio="voucher",
            codigo_voucher="ADAPTER10",
        )

        self.voucher.refresh_from_db()
        self.assertEqual(self.voucher.total_utilizado, 0)
        self.assertEqual(self.voucher.usos.count(), 0)

    def test_cashback_respeita_limite_central(self):
        with self.assertRaises(ValidationError):
            resolver_beneficio_da_venda(
                matriz=self.matriz,
                loja=self.loja,
                valor_compra=Decimal("100.00"),
                tipo_beneficio="cashback",
                valor_cashback=Decimal("31.00"),
            )

    def test_voucher_respeita_limite_central(self):
        self.voucher.percentual = Decimal("40.00")
        self.voucher.save(update_fields=["percentual", "atualizado_em"])

        with self.assertRaises(ValidationError):
            resolver_beneficio_da_venda(
                matriz=self.matriz,
                loja=self.loja,
                valor_compra=Decimal("100.00"),
                tipo_beneficio="voucher",
                codigo_voucher="ADAPTER10",
            )

    def test_tipo_invalido_e_rejeitado(self):
        with self.assertRaises(ValidationError):
            resolver_beneficio_da_venda(
                matriz=self.matriz,
                loja=self.loja,
                valor_compra=Decimal("100.00"),
                tipo_beneficio="brinde",
            )

    @patch("pdv.services.vendas.beneficios.registrar_uso_voucher")
    def test_registro_delega_ao_servico_oficial(self, registrar_mock):
        venda = Venda.objects.create(
            matriz=self.matriz,
            loja=self.loja,
            operador=self.usuario,
            cliente=self.cliente,
            subtotal=Decimal("100.00"),
            total=Decimal("100.00"),
        )
        compra = object()
        uso_esperado = object()
        registrar_mock.return_value = uso_esperado

        beneficio = BeneficioResolvido(
            tipo="voucher",
            valor=Decimal("10.00"),
            voucher=self.voucher,
            codigo=self.voucher.codigo,
        )

        uso = registrar_voucher_da_venda(
            venda=venda,
            usuario=self.usuario,
            beneficio=beneficio,
            compra=compra,
        )

        self.assertIs(uso, uso_esperado)
        registrar_mock.assert_called_once_with(
            matriz=self.matriz,
            loja=self.loja,
            cliente=self.cliente,
            voucher=self.voucher,
            usuario=self.usuario,
            compra=compra,
            valor_compra=Decimal("100.00"),
            valor_desconto=Decimal("10.00"),
            observacao=f"Voucher utilizado na venda PDV #{venda.pk}.",
        )

    @patch("pdv.services.vendas.beneficios.registrar_uso_voucher")
    def test_beneficio_nao_voucher_nao_registra(self, registrar_mock):
        venda = Venda.objects.create(
            matriz=self.matriz,
            loja=self.loja,
            operador=self.usuario,
            cliente=self.cliente,
            subtotal=Decimal("100.00"),
            total=Decimal("100.00"),
        )

        uso = registrar_voucher_da_venda(
            venda=venda,
            usuario=self.usuario,
            beneficio=BeneficioResolvido.nenhum(),
            compra=None,
        )

        self.assertIsNone(uso)
        registrar_mock.assert_not_called()
