from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import Usuario
from clientes.models import Cliente
from empresas.models import Loja, Matriz
from core.choices import StatusOperacional
from vouchers.models import Voucher


class Cliente360VouchersUX195F416G19Tests(TestCase):
    def setUp(self):
        self.matriz = Matriz.objects.create(nome="Matriz G19")
        self.loja_a = Loja.objects.create(
            matriz=self.matriz,
            nome="Loja A G19",
            status=StatusOperacional.ATIVA,
        )
        self.usuario = Usuario.objects.create_user(
            username="usuario_g19",
            password="senha-g19",
            matriz=self.matriz,
        )
        self.usuario.lojas.add(self.loja_a)
        self.cliente = Cliente.objects.create(
            matriz=self.matriz,
            loja_cadastro=self.loja_a,
            nome="Cliente G19",
            cpf="52998224725",
            telefone="11999999999",
        )
        self.url = reverse("clientes:extrato_cliente", args=[self.cliente.id])
        self.hoje = timezone.localdate()

    def voucher(self, *, codigo, cliente=None, status=Voucher.Status.ATIVO,
                inicio=None, fim=None):
        return Voucher.objects.create(
            matriz=self.matriz,
            cliente=cliente,
            codigo=codigo,
            nome=codigo,
            tipo=Voucher.Tipo.VALOR_FIXO,
            valor="10.00",
            status=status,
            data_inicio=inicio or self.hoje,
            data_fim=fim or (self.hoje + timedelta(days=30)),
            limite_utilizacao=1,
            total_utilizado=0,
        )

    def entrar(self):
        self.client.force_login(self.usuario)

    def test_lista_vouchers_inclui_especifico_e_global_da_mesma_matriz(self):
        especifico = self.voucher(codigo="G19-ESP", cliente=self.cliente)
        global_matriz = self.voucher(codigo="G19-GLOBAL")

        self.entrar()
        response = self.client.get(self.url, {"secao": "vouchers"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["dominio_ativo"], "vouchers")
        page = response.context["vouchers_page"]
        self.assertIn(especifico, list(page.object_list))
        self.assertIn(global_matriz, list(page.object_list))

    def test_nao_vaza_voucher_de_outro_cliente_ou_outra_matriz(self):
        outro_cliente = Cliente.objects.create(
            matriz=self.matriz,
            loja_cadastro=self.loja_a,
            nome="Outro Cliente G19",
            cpf="12345678909",
            telefone="11888888888",
        )
        alheio = self.voucher(codigo="G19-ALHEIO", cliente=outro_cliente)

        outra_matriz = Matriz.objects.create(nome="Outra Matriz G19")
        loja_b = Loja.objects.create(matriz=outra_matriz, nome="Loja B G19")
        cliente_b = Cliente.objects.create(
            matriz=outra_matriz,
            loja_cadastro=loja_b,
            nome="Cliente Outra Matriz G19",
            cpf="11144477735",
            telefone="11777777777",
        )
        externo = Voucher.objects.create(
            matriz=outra_matriz,
            cliente=cliente_b,
            codigo="G19-EXTERNO",
            nome="G19-EXTERNO",
            tipo=Voucher.Tipo.VALOR_FIXO,
            valor="10.00",
            status=Voucher.Status.ATIVO,
            data_inicio=self.hoje,
            data_fim=self.hoje + timedelta(days=30),
            limite_utilizacao=1,
            total_utilizado=0,
        )

        self.entrar()
        response = self.client.get(self.url, {"secao": "vouchers"})
        objetos = list(response.context["vouchers_page"].object_list)

        self.assertNotIn(alheio, objetos)
        self.assertNotIn(externo, objetos)

    def test_filtro_status_ativo_e_inativo(self):
        ativo = self.voucher(codigo="G19-ATIVO")
        inativo = self.voucher(codigo="G19-INATIVO", status=Voucher.Status.INATIVO)

        self.entrar()
        response = self.client.get(
            self.url,
            {"secao": "vouchers", "status": Voucher.Status.INATIVO},
        )
        objetos = list(response.context["vouchers_page"].object_list)

        self.assertIn(inativo, objetos)
        self.assertNotIn(ativo, objetos)

    def test_filtro_periodo_por_intersecao_da_validade_e_inclusivo(self):
        inicio_filtro = self.hoje + timedelta(days=10)
        fim_filtro = self.hoje + timedelta(days=20)

        sobrepoe_inicio = self.voucher(
            codigo="G19-SOBREPOE-INICIO",
            inicio=self.hoje,
            fim=inicio_filtro,
        )
        dentro = self.voucher(
            codigo="G19-DENTRO",
            inicio=inicio_filtro + timedelta(days=1),
            fim=fim_filtro - timedelta(days=1),
        )
        sobrepoe_fim = self.voucher(
            codigo="G19-SOBREPOE-FIM",
            inicio=fim_filtro,
            fim=fim_filtro + timedelta(days=10),
        )
        fora = self.voucher(
            codigo="G19-FORA",
            inicio=fim_filtro + timedelta(days=1),
            fim=fim_filtro + timedelta(days=20),
        )

        self.entrar()
        response = self.client.get(
            self.url,
            {
                "secao": "vouchers",
                "data_inicio": inicio_filtro.isoformat(),
                "data_fim": fim_filtro.isoformat(),
            },
        )
        objetos = list(response.context["vouchers_page"].object_list)

        self.assertIn(sobrepoe_inicio, objetos)
        self.assertIn(dentro, objetos)
        self.assertIn(sobrepoe_fim, objetos)
        self.assertNotIn(fora, objetos)

    def test_paginacao_vouchers_vinte_por_pagina(self):
        for i in range(21):
            self.voucher(codigo=f"G19-PAG-{i:02d}")

        self.entrar()
        primeira = self.client.get(self.url, {"secao": "vouchers"})
        segunda = self.client.get(self.url, {"secao": "vouchers", "page": "2"})

        self.assertEqual(len(primeira.context["vouchers_page"].object_list), 20)
        self.assertEqual(primeira.context["vouchers_page"].paginator.count, 21)
        self.assertEqual(len(segunda.context["vouchers_page"].object_list), 1)

    def test_parametros_invalidos_sao_seguros_e_querystring_preserva_filtros_sem_page(self):
        self.voucher(codigo="G19-SEGURO")

        self.entrar()
        response = self.client.get(
            self.url,
            {
                "secao": "vouchers",
                "data_inicio": "nao-e-data",
                "data_fim": "tambem-nao",
                "status": "status-inexistente",
                "page": "2",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["vouchers_page"].paginator.count, 1)

        query = response.context["query_string_vouchers"]
        self.assertIn("secao=vouchers", query)
        self.assertIn("data_inicio=nao-e-data", query)
        self.assertIn("data_fim=tambem-nao", query)
        self.assertIn("status=status-inexistente", query)
        self.assertNotIn("page=", query)