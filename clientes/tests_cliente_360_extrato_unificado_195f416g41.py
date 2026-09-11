from django.test import TestCase

from clientes.tests_cliente_360_ux_extratos_195f416g4 import Cliente360UXExtratosTests


class Cliente360ExtratoUnificado195F416G41Tests(Cliente360UXExtratosTests):
    def test_secao_padrao_e_extrato_e_nao_visao_geral(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["dominio_ativo"], "extrato")
        self.assertContains(response, 'data-cliente360-secao="extrato"')
        self.assertNotContains(response, 'data-cliente360-secao="visao-geral"')

    def test_extrato_tem_filtros_de_data_e_paginacao_propria(self):
        response = self.client.get(self.url, {"secao": "extrato"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("filtros_extrato", response.context)
        self.assertIn("extrato_page", response.context)
        self.assertIn("query_string_extrato", response.context)
        self.assertContains(response, 'name="data_inicio"')
        self.assertContains(response, 'name="data_fim"')

    def test_extrato_nao_carrega_cliente360_compras(self):
        response = self.client.get(self.url, {"secao": "extrato"})
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context.get("cliente_360"))

    def test_extrato_renderiza_componente_dedicado(self):
        response = self.client.get(self.url, {"secao": "extrato"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'data-cliente360-extrato="lista"')
        self.assertContains(response, "Extrato")
        self.assertNotContains(response, "Visão geral")
