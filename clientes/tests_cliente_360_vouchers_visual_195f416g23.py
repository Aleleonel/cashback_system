from pathlib import Path
from django.test import TestCase
from django.urls import reverse

from accounts.models import Usuario
from clientes.models import Cliente
from core.choices import StatusOperacional
from empresas.models import Loja, Matriz


class Cliente360VouchersVisual195F416G23Tests(TestCase):
    def setUp(self):
        self.matriz = Matriz.objects.create(nome="Matriz G23")
        self.loja = Loja.objects.create(
            matriz=self.matriz,
            nome="Loja G23",
            status=StatusOperacional.ATIVA,
        )
        self.usuario = Usuario.objects.create_user(
            username="usuario_g23",
            password="senha-g23",
            matriz=self.matriz,
        )
        self.usuario.lojas.add(self.loja)

        self.cliente = Cliente.objects.create(
            matriz=self.matriz,
            loja_cadastro=self.loja,
            nome="Cliente G23",
            cpf="39053344705",
            telefone="11999999999",
        )

        self.client.force_login(self.usuario)
        self.url = reverse("clientes:extrato_cliente", args=[self.cliente.id])

    def get_vouchers(self):
        return self.client.get(self.url, {"secao": "vouchers"})

    def test_exibe_secao_dedicada_de_vouchers(self):
        response = self.get_vouchers()
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'data-cliente360-vouchers="lista"')

    def test_exibe_formulario_get_com_filtros_de_data_e_status(self):
        response = self.get_vouchers()
        self.assertContains(response, 'name="secao" value="vouchers"')
        self.assertContains(response, 'name="data_inicio"')
        self.assertContains(response, 'name="data_fim"')
        self.assertContains(response, 'name="status"')

    def test_exibe_estrutura_de_tabela_de_vouchers(self):
        response = self.get_vouchers()
        self.assertContains(response, "Código")
        self.assertContains(response, "Nome")
        self.assertContains(response, "Validade")
        self.assertContains(response, "Status")
        self.assertContains(response, "Benefício")

    def test_exibe_estado_vazio_especifico_sem_vouchers(self):
        response = self.get_vouchers()
        self.assertContains(response, "Nenhum voucher encontrado")

    def test_contrato_visual_expoe_paginacao_por_query_string_vouchers(self):
        response = self.get_vouchers()
        self.assertIn("query_string_vouchers", response.context)
        template = Path("clientes/templates/clientes/extrato_cliente.html").read_text(encoding="utf-8")
        self.assertIn("?{{ query_string_vouchers }}&page=", template)


    def test_exibe_percentual_real_do_beneficio_voucher(self):
        from decimal import Decimal
        from datetime import timedelta
        from django.utils import timezone
        from vouchers.models import Voucher

        Voucher.objects.create(
            matriz=self.matriz,
            cliente=self.cliente,
            codigo="PERCENTUAL-G37",
            nome="Voucher percentual G37",
            tipo=Voucher.Tipo.PERCENTUAL,
            percentual=Decimal("12.50"),
            data_fim=timezone.localdate() + timedelta(days=30),
            status=Voucher.Status.ATIVO,
        )

        response = self.client.get(
            self.url,
            {"secao": "vouchers"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "12,50%")

    def test_exibe_valor_real_do_beneficio_voucher(self):
        from datetime import timedelta
        from django.utils import timezone
        from vouchers.models import Voucher

        hoje = timezone.localdate()
        Voucher.objects.create(
            matriz=self.matriz, cliente=self.cliente, codigo='G29-VALOR-REAL',
            nome='Voucher valor real', tipo=Voucher.Tipo.VALOR_FIXO, valor='17.35',
            status=Voucher.Status.ATIVO, data_inicio=hoje, data_fim=hoje + timedelta(days=30),
            limite_utilizacao=1, total_utilizado=0,
        )
        response = self.get_vouchers()
        self.assertContains(response, '17,35')
