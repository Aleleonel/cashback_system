from datetime import datetime
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from clientes.models import Cliente
from core.choices import StatusOperacional
from empresas.models import Loja, Matriz
from pdv.models import Venda


class Cliente360ComprasUXTests(TestCase):
    def setUp(self):
        self.matriz = Matriz.objects.create(nome="Matriz Compras UX")
        self.loja_origem = Loja.objects.create(
            matriz=self.matriz,
            nome="Loja Origem Compras UX",
            status=StatusOperacional.ATIVA,
        )
        self.loja_b = Loja.objects.create(
            matriz=self.matriz,
            nome="Loja B Compras UX",
            status=StatusOperacional.ATIVA,
        )
        self.outra_matriz = Matriz.objects.create(nome="Outra Matriz Compras UX")
        self.loja_externa = Loja.objects.create(
            matriz=self.outra_matriz,
            nome="Loja Externa Compras UX",
            status=StatusOperacional.ATIVA,
        )

        User = get_user_model()
        self.usuario = User.objects.create_user(
            username="usuario_compras_ux",
            password="teste123",
            perfil=User.PERFIL_OPERADOR,
            matriz=self.matriz,
        )
        self.usuario.lojas.add(self.loja_origem, self.loja_b)

        self.operador = self.usuario
        self.cliente = Cliente.objects.create(
            matriz=self.matriz,
            loja_cadastro=self.loja_origem,
            nome="Cliente Compras UX",
            cpf="52998224725",
            tipo_pessoa="PF",
        )
        self.outro_cliente = Cliente.objects.create(
            matriz=self.matriz,
            loja_cadastro=self.loja_origem,
            nome="Outro Cliente Compras UX",
            cpf="11144477735",
            tipo_pessoa="PF",
        )
        self.client.force_login(self.usuario)
        self.url = reverse("clientes:extrato_cliente", args=[self.cliente.id])

    def momento(self, ano, mes, dia, hora=12):
        return timezone.make_aware(datetime(ano, mes, dia, hora, 0, 0))

    def venda(self, *, loja=None, cliente=None, status="finalizada",
              total="100.00", finalizada_em=None):
        venda = Venda.objects.create(
            matriz=self.matriz,
            loja=loja or self.loja_origem,
            cliente=cliente or self.cliente,
            operador=self.operador,
            subtotal=Decimal(total),
            total=Decimal(total),
            status=status,
            finalizada_em=finalizada_em,
        )
        return venda

    def get_compras(self, **params):
        query = {"secao": "compras"}
        query.update(params)
        response = self.client.get(self.url, query)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["dominio_ativo"], "compras")
        self.assertIn("compras_page", response.context)
        self.assertIn("filtros_compras", response.context)
        self.assertIn("lojas_compras", response.context)
        self.assertIn("query_string_compras", response.context)
        return response, response.context["compras_page"]

    def test_compras_exibe_finalizadas_de_lojas_distintas_da_mesma_matriz(self):
        a = self.venda(
            loja=self.loja_origem,
            total="100.00",
            finalizada_em=self.momento(2026, 9, 1),
        )
        b = self.venda(
            loja=self.loja_b,
            total="200.00",
            finalizada_em=self.momento(2026, 9, 2),
        )
        self.venda(
            loja=self.loja_b,
            status="cancelada",
            total="300.00",
            finalizada_em=None,
        )
        self.venda(
            loja=self.loja_b,
            cliente=self.outro_cliente,
            total="400.00",
            finalizada_em=self.momento(2026, 9, 3),
        )

        _, page = self.get_compras()
        ids = [v.id for v in page.object_list]

        self.assertEqual(set(ids), {a.id, b.id})
        self.assertEqual(ids[0], b.id)
        self.assertEqual(ids[1], a.id)

    def test_filtro_data_inicio_e_inclusivo_por_finalizada_em(self):
        antiga = self.venda(finalizada_em=self.momento(2026, 8, 31))
        inicio = self.venda(finalizada_em=self.momento(2026, 9, 1))
        depois = self.venda(finalizada_em=self.momento(2026, 9, 2))

        _, page = self.get_compras(data_inicio="2026-09-01")
        ids = {v.id for v in page.object_list}

        self.assertNotIn(antiga.id, ids)
        self.assertEqual(ids, {inicio.id, depois.id})

    def test_filtro_data_fim_e_inclusivo_por_finalizada_em(self):
        antes = self.venda(finalizada_em=self.momento(2026, 8, 31))
        fim = self.venda(finalizada_em=self.momento(2026, 9, 1, 23))
        depois = self.venda(finalizada_em=self.momento(2026, 9, 2))

        _, page = self.get_compras(data_fim="2026-09-01")
        ids = {v.id for v in page.object_list}

        self.assertEqual(ids, {antes.id, fim.id})
        self.assertNotIn(depois.id, ids)

    def test_filtro_loja_usa_loja_da_transacao_e_nao_loja_cadastro(self):
        origem = self.venda(
            loja=self.loja_origem,
            finalizada_em=self.momento(2026, 9, 1),
        )
        loja_b = self.venda(
            loja=self.loja_b,
            finalizada_em=self.momento(2026, 9, 2),
        )

        _, page = self.get_compras(loja=str(self.loja_b.id))
        ids = [v.id for v in page.object_list]

        self.assertEqual(ids, [loja_b.id])
        self.assertNotIn(origem.id, ids)

    def test_combina_periodo_e_loja_sem_restringir_por_loja_cadastro(self):
        self.venda(
            loja=self.loja_b,
            finalizada_em=self.momento(2026, 8, 31),
        )
        alvo = self.venda(
            loja=self.loja_b,
            finalizada_em=self.momento(2026, 9, 5),
        )
        self.venda(
            loja=self.loja_origem,
            finalizada_em=self.momento(2026, 9, 5),
        )
        self.venda(
            loja=self.loja_b,
            finalizada_em=self.momento(2026, 9, 11),
        )

        _, page = self.get_compras(
            data_inicio="2026-09-01",
            data_fim="2026-09-10",
            loja=str(self.loja_b.id),
        )

        self.assertEqual([v.id for v in page.object_list], [alvo.id])

    def test_paginacao_tem_20_registros_e_segunda_pagina(self):
        for dia in range(1, 26):
            self.venda(
                loja=self.loja_b if dia % 2 == 0 else self.loja_origem,
                total=str(100 + dia),
                finalizada_em=self.momento(2026, 8, dia),
            )

        _, page1 = self.get_compras()
        _, page2 = self.get_compras(page="2")

        self.assertEqual(page1.paginator.per_page, 20)
        self.assertEqual(page1.paginator.count, 25)
        self.assertEqual(len(page1.object_list), 20)
        self.assertEqual(page1.number, 1)
        self.assertEqual(page2.number, 2)
        self.assertEqual(len(page2.object_list), 5)

    def test_query_string_de_paginacao_preserva_secao_e_filtros_sem_page(self):
        self.venda(
            loja=self.loja_b,
            finalizada_em=self.momento(2026, 9, 5),
        )

        response, _ = self.get_compras(
            data_inicio="2026-09-01",
            data_fim="2026-09-10",
            loja=str(self.loja_b.id),
            page="2",
        )
        query_string = response.context["query_string_compras"]

        self.assertIn("secao=compras", query_string)
        self.assertIn("data_inicio=2026-09-01", query_string)
        self.assertIn("data_fim=2026-09-10", query_string)
        self.assertIn("loja=" + str(self.loja_b.id), query_string)
        self.assertNotIn("page=", query_string)

    def test_parametros_invalidos_ou_loja_externa_nao_vazam_dados(self):
        propria = self.venda(
            loja=self.loja_b,
            finalizada_em=self.momento(2026, 9, 5),
        )

        response, page = self.get_compras(
            data_inicio="invalida",
            data_fim="31-12-2026",
            loja=str(self.loja_externa.id),
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(all(v.matriz_id == self.matriz.id for v in page.object_list))
        self.assertNotIn(
            self.loja_externa.id,
            {v.loja_id for v in page.object_list},
        )
        self.assertIn(propria.id, {v.id for v in page.object_list})