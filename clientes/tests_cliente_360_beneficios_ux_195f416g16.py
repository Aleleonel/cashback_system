from datetime import datetime, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from cashback.models import LancamentoCashback, UsoCashback
from clientes.models import Cliente
from core.choices import StatusOperacional
from empresas.models import Loja, Matriz


class Cliente360BeneficiosUXTests(TestCase):
    def setUp(self):
        self.matriz = Matriz.objects.create(nome="Matriz Beneficios UX")
        self.loja_origem = Loja.objects.create(
            matriz=self.matriz,
            nome="Loja Origem Beneficios UX",
            status=StatusOperacional.ATIVA,
        )
        self.loja_b = Loja.objects.create(
            matriz=self.matriz,
            nome="Loja B Beneficios UX",
            status=StatusOperacional.ATIVA,
        )

        User = get_user_model()
        self.usuario = User.objects.create_user(
            username="usuario_beneficios_ux",
            password="teste123",
            perfil=User.PERFIL_OPERADOR,
            matriz=self.matriz,
        )
        self.usuario.lojas.add(self.loja_origem)

        self.cliente = Cliente.objects.create(
            matriz=self.matriz,
            loja_cadastro=self.loja_origem,
            nome="Cliente Beneficios UX",
            cpf="52998224725",
            tipo_pessoa="PF",
        )

        self.client.force_login(self.usuario)
        self.url = reverse("clientes:extrato_cliente", args=[self.cliente.id])

    def momento(self, ano, mes, dia, hora=12):
        return timezone.make_aware(datetime(ano, mes, dia, hora, 0, 0))

    def lancamento(self, *, criado_em, loja=None, valor="10.00"):
        hoje = timezone.localdate()
        obj = LancamentoCashback.objects.create(
            matriz=self.matriz,
            loja=loja or self.loja_b,
            cliente=self.cliente,
            valor_compra=Decimal("100.00"),
            valor_base_cashback=Decimal("100.00"),
            percentual_cashback=Decimal("10.00"),
            valor_cashback=Decimal(valor),
            valor_utilizado=Decimal("0.00"),
            data_compra=criado_em.date(),
            data_liberacao=hoje - timedelta(days=1),
            data_expiracao=hoje + timedelta(days=30),
        )
        LancamentoCashback.objects.filter(pk=obj.pk).update(criado_em=criado_em)
        obj.refresh_from_db()
        return obj

    def uso(self, *, criado_em, loja=None, valor="5.00"):
        obj = UsoCashback.objects.create(
            matriz=self.matriz,
            loja=loja or self.loja_b,
            cliente=self.cliente,
            valor_usado=Decimal(valor),
            observacao="Uso cashback UX",
        )
        UsoCashback.objects.filter(pk=obj.pk).update(data_uso=criado_em)
        obj.refresh_from_db()
        return obj

    def get_beneficios(self, **params):
        query = {"secao": "beneficios"}
        query.update(params)
        response = self.client.get(self.url, query)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["dominio_ativo"], "beneficios")
        self.assertIn("beneficios_page", response.context)
        self.assertIn("filtros_beneficios", response.context)
        self.assertIn("query_string_beneficios", response.context)
        return response, response.context["beneficios_page"]

    def test_beneficios_expoe_credito_e_debito_cashback_da_mesma_matriz(self):
        entrada = self.lancamento(
            criado_em=self.momento(2026, 9, 1),
            loja=self.loja_b,
            valor="20.00",
        )
        saida = self.uso(
            criado_em=self.momento(2026, 9, 2),
            loja=self.loja_b,
            valor="5.00",
        )

        _, page = self.get_beneficios()
        itens = list(page.object_list)

        self.assertEqual([i["tipo"] for i in itens], ["SAIDA", "ENTRADA"])
        self.assertEqual(itens[0]["referencia"].id, saida.id)
        self.assertEqual(itens[1]["referencia"].id, entrada.id)
        self.assertTrue(all(i["loja"].id == self.loja_b.id for i in itens))

    def test_filtro_data_inicio_e_inclusivo(self):
        self.lancamento(criado_em=self.momento(2026, 8, 31))
        inicio = self.lancamento(criado_em=self.momento(2026, 9, 1))
        depois = self.uso(criado_em=self.momento(2026, 9, 2))

        _, page = self.get_beneficios(data_inicio="2026-09-01")
        ids = {(i["tipo"], i["referencia"].id) for i in page.object_list}

        self.assertEqual(ids, {("ENTRADA", inicio.id), ("SAIDA", depois.id)})

    def test_filtro_data_fim_e_inclusivo(self):
        antes = self.lancamento(criado_em=self.momento(2026, 8, 31))
        fim = self.uso(criado_em=self.momento(2026, 9, 1, 23))
        self.lancamento(criado_em=self.momento(2026, 9, 2))

        _, page = self.get_beneficios(data_fim="2026-09-01")
        ids = {(i["tipo"], i["referencia"].id) for i in page.object_list}

        self.assertEqual(ids, {("ENTRADA", antes.id), ("SAIDA", fim.id)})

    def test_paginacao_tem_20_registros_e_segunda_pagina(self):
        for dia in range(1, 26):
            self.lancamento(
                criado_em=self.momento(2026, 8, dia),
                valor=str(10 + dia),
            )

        _, page1 = self.get_beneficios()
        _, page2 = self.get_beneficios(page="2")

        self.assertEqual(page1.paginator.per_page, 20)
        self.assertEqual(page1.paginator.count, 25)
        self.assertEqual(len(page1.object_list), 20)
        self.assertEqual(page1.number, 1)
        self.assertEqual(page2.number, 2)
        self.assertEqual(len(page2.object_list), 5)

    def test_query_string_preserva_secao_e_filtros_sem_page(self):
        self.lancamento(criado_em=self.momento(2026, 9, 5))

        response, _ = self.get_beneficios(
            data_inicio="2026-09-01",
            data_fim="2026-09-10",
            page="2",
        )

        qs = response.context["query_string_beneficios"]
        self.assertIn("secao=beneficios", qs)
        self.assertIn("data_inicio=2026-09-01", qs)
        self.assertIn("data_fim=2026-09-10", qs)
        self.assertNotIn("page=", qs)

    def test_parametros_de_data_invalidos_nao_quebram_nem_vazam_dados(self):
        propria = self.lancamento(criado_em=self.momento(2026, 9, 5))

        response, page = self.get_beneficios(
            data_inicio="invalida",
            data_fim="31-12-2026",
        )

        self.assertEqual(response.status_code, 200)
        ids = {i["referencia"].id for i in page.object_list}
        self.assertIn(propria.id, ids)
        self.assertTrue(all(i["referencia"].matriz_id == self.matriz.id for i in page.object_list))