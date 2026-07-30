from datetime import timedelta
from decimal import Decimal
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from cashback.models import LancamentoCashback
from clientes.models import Cliente
from empresas.models import Loja, Matriz
from vouchers.models import UsoVoucher, Voucher
from vouchers.services import registrar_uso_voucher


class VoucherRegraCompartilhadaCaracterizacaoTests(TestCase):
    def setUp(self):
        self.matriz = Matriz.objects.create(nome="Matriz Caracterizacao")
        self.loja = Loja.objects.create(matriz=self.matriz, nome="Loja Caracterizacao")
        self.cliente = Cliente.objects.create(
            matriz=self.matriz,
            loja_cadastro=self.loja,
            nome="Cliente Caracterizacao",
            cpf="12345678901",
        )
        self.outro_cliente = Cliente.objects.create(
            matriz=self.matriz,
            loja_cadastro=self.loja,
            nome="Outro Cliente",
            cpf="10987654321",
        )
        self.usuario = get_user_model().objects.create_user(
            username="operador_caracterizacao",
            password="senha-teste",
            matriz=self.matriz,
        )
        self.usuario.lojas.add(self.loja)
        self.hoje = timezone.localdate()

    def criar_voucher(
        self,
        *,
        codigo,
        limite=2,
        total_utilizado=0,
        uso_unico_por_cliente=False,
        cliente=None,
    ):
        return Voucher.objects.create(
            matriz=self.matriz,
            cliente=cliente,
            codigo=codigo,
            nome=f"Voucher {codigo}",
            tipo=Voucher.Tipo.VALOR_FIXO,
            valor=Decimal("10.00"),
            data_inicio=self.hoje,
            data_fim=self.hoje + timedelta(days=30),
            limite_utilizacao=limite,
            total_utilizado=total_utilizado,
            uso_unico_por_cliente=uso_unico_por_cliente,
        )

    def criar_compra(self, *, cliente, valor="100.00"):
        return LancamentoCashback.objects.create(
            matriz=self.matriz,
            loja=self.loja,
            cliente=cliente,
            valor_compra=Decimal(valor),
            valor_base_cashback=Decimal(valor),
            percentual_cashback=Decimal("5.00"),
            valor_cashback=Decimal("5.00"),
            valor_utilizado=Decimal("0.00"),
            data_compra=self.hoje,
            data_liberacao=self.hoje,
            data_expiracao=self.hoje + timedelta(days=30),
        )

    def registrar(self, *, voucher, cliente):
        compra = self.criar_compra(cliente=cliente)
        return registrar_uso_voucher(
            matriz=self.matriz,
            loja=self.loja,
            cliente=cliente,
            voucher=voucher,
            usuario=self.usuario,
            compra=compra,
            valor_compra=Decimal("100.00"),
            valor_desconto=Decimal("10.00"),
            observacao="Teste de caracterizacao.",
        )

    def test_voucher_um_de_dois_aceita_segundo_uso(self):
        voucher = self.criar_voucher(
            codigo="CARAC-1-DE-2",
            limite=2,
            total_utilizado=1,
            uso_unico_por_cliente=False,
        )
        uso = self.registrar(voucher=voucher, cliente=self.cliente)
        voucher.refresh_from_db()
        self.assertIsNotNone(uso.pk)
        self.assertEqual(voucher.total_utilizado, 2)

    def test_voucher_dois_de_dois_bloqueia_terceiro_uso(self):
        voucher = self.criar_voucher(
            codigo="CARAC-2-DE-2",
            limite=2,
            total_utilizado=2,
            uso_unico_por_cliente=False,
        )
        with self.assertRaises(ValidationError):
            self.registrar(voucher=voucher, cliente=self.cliente)
        voucher.refresh_from_db()
        self.assertEqual(voucher.total_utilizado, 2)
        self.assertEqual(voucher.usos.count(), 0)

    def test_voucher_nao_unico_permite_mesmo_cliente_duas_vezes(self):
        voucher = self.criar_voucher(
            codigo="CARAC-REPETE",
            limite=3,
            uso_unico_por_cliente=False,
        )
        self.registrar(voucher=voucher, cliente=self.cliente)
        self.registrar(voucher=voucher, cliente=self.cliente)
        voucher.refresh_from_db()
        self.assertEqual(voucher.total_utilizado, 2)
        self.assertEqual(
            UsoVoucher.objects.filter(voucher=voucher, cliente=self.cliente).count(),
            2,
        )

    def test_voucher_uso_unico_bloqueia_segundo_uso_do_mesmo_cliente(self):
        voucher = self.criar_voucher(
            codigo="CARAC-UNICO",
            limite=3,
            uso_unico_por_cliente=True,
        )
        self.registrar(voucher=voucher, cliente=self.cliente)
        with self.assertRaisesMessage(
            ValidationError,
            "Este cliente ja utilizou este voucher.",
        ):
            self.registrar(voucher=voucher, cliente=self.cliente)
        voucher.refresh_from_db()
        self.assertEqual(voucher.total_utilizado, 1)

    def test_voucher_uso_unico_permite_clientes_diferentes(self):
        voucher = self.criar_voucher(
            codigo="CARAC-UNICO-DIF",
            limite=3,
            uso_unico_por_cliente=True,
        )
        self.registrar(voucher=voucher, cliente=self.cliente)
        self.registrar(voucher=voucher, cliente=self.outro_cliente)
        voucher.refresh_from_db()
        self.assertEqual(voucher.total_utilizado, 2)
        self.assertEqual(voucher.usos.count(), 2)

    def test_voucher_vinculado_a_cliente_bloqueia_outro_cliente(self):
        voucher = self.criar_voucher(
            codigo="CARAC-CLIENTE",
            limite=2,
            uso_unico_por_cliente=False,
            cliente=self.cliente,
        )
        with self.assertRaisesMessage(
            ValidationError,
            "Este voucher pertence a outro cliente.",
        ):
            self.registrar(voucher=voucher, cliente=self.outro_cliente)
        voucher.refresh_from_db()
        self.assertEqual(voucher.total_utilizado, 0)

    def test_uso_oficial_fica_vinculado_a_compra(self):
        voucher = self.criar_voucher(
            codigo="CARAC-COMPRA",
            limite=2,
            uso_unico_por_cliente=False,
        )
        uso = self.registrar(voucher=voucher, cliente=self.cliente)
        self.assertIsNotNone(uso.compra_id)
        self.assertEqual(uso.compra.cliente, self.cliente)


class PdvContratoRefatoracaoCaracterizacaoTests(TestCase):
    @staticmethod
    def ler(caminho):
        raiz = Path(__file__).resolve().parents[2]
        return (raiz / caminho).read_text(encoding="utf-8")

    def test_model_venda_mantem_campos_de_desconto(self):
        from pdv.models import Venda
        campos = {field.name for field in Venda._meta.get_fields()}
        self.assertIn("desconto", campos)
        self.assertIn("desconto_geral", campos)

    def test_template_expoe_campo_desconto_geral_no_fechamento(self):
        template = self.ler("pdv/templates/pdv/inicio.html")
        self.assertIn('id="pdv-desconto-geral"', template)
        self.assertIn('name="desconto_geral"', template)

    def test_javascript_envia_desconto_geral_no_payload(self):
        javascript = self.ler("pdv/static/pdv/js/frente_caixa.js")
        self.assertIn("desconto_geral", javascript)
        self.assertIn("pdv-desconto-geral", javascript)

    def test_pdv_nao_cria_uso_voucher_diretamente(self):
        fechamento = self.ler("pdv/services/vendas/fechamento.py")
        self.assertNotIn("UsoVoucher.objects.create", fechamento)
        self.assertNotIn("def _registrar_uso_voucher", fechamento)

    def test_pdv_reutiliza_fluxo_oficial_de_beneficios(self):
        fechamento = self.ler("pdv/services/vendas/fechamento.py")
        beneficios = self.ler("pdv/services/vendas/beneficios.py")

        self.assertIn("resolver_beneficio_da_venda", fechamento)
        self.assertIn("executar_venda_idempotente", fechamento)
        self.assertNotIn("UsoVoucher.objects.create", fechamento)
        self.assertNotIn("def _registrar_uso_voucher", fechamento)

        self.assertIn("registrar_voucher_da_venda", beneficios)
        self.assertIn("registrar_uso_voucher", beneficios)
        self.assertIn("from vouchers.services", beneficios)

    def test_view_pdv_nao_duplica_regra_de_uso_unico(self):
        views = self.ler("pdv/views.py")
        self.assertNotIn("UsoVoucher.objects.filter", views)
        self.assertNotIn("uso_unico_por_cliente", views)

    def test_view_pdv_nao_duplica_calculo_do_desconto_voucher(self):
        views = self.ler("pdv/views.py")
        self.assertNotIn("total * (voucher.percentual", views)
