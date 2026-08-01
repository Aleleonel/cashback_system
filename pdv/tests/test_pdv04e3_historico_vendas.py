from pathlib import Path

from django.test import SimpleTestCase


class Pdv04E3HistoricoVendasContratoTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.views = Path("pdv/views.py").read_text(encoding="utf-8")
        cls.urls = Path("pdv/urls.py").read_text(encoding="utf-8")
        cls.sidebar = Path("templates/partials/sidebar.html").read_text(encoding="utf-8")
        cls.lista = Path("pdv/templates/pdv/historico_vendas.html").read_text(encoding="utf-8")
        cls.detalhe = Path("pdv/templates/pdv/detalhe_venda.html").read_text(encoding="utf-8")

    def test_rotas_nomeadas_existem(self):
        self.assertIn('name="historico_vendas"', self.urls)
        self.assertIn('name="detalhe_venda"', self.urls)

    def test_views_sao_protegidas(self):
        self.assertIn("def historico_vendas(request):", self.views)
        self.assertIn("def detalhe_venda(request, venda_uuid):", self.views)
        self.assertGreaterEqual(
            self.views.count("@require_permission(PERMISSAO_PDV_VISUALIZAR)"),
            2,
        )

    def test_consulta_isola_matriz_e_lojas(self):
        self.assertIn("matriz=matriz", self.views)
        self.assertIn("loja__in=lojas", self.views)
        self.assertIn("uuid=venda_uuid", self.views)

    def test_lista_exibe_apenas_vendas_encerradas(self):
        self.assertIn("StatusOperacaoVenda.FINALIZADA", self.views)
        self.assertIn("StatusOperacaoVenda.CANCELADA", self.views)

    def test_filtros_existem(self):
        for campo in (
            "data_inicio", "data_fim", "numero", "cliente",
            "vendedor", "operador", "status",
            "forma_pagamento", "caixa", "loja",
        ):
            self.assertIn(f'name="{campo}"', self.lista)

    def test_paginacao_e_totais_existem(self):
        self.assertIn("Paginator(vendas, 20)", self.views)
        for campo in (
            "total_vendas", "valor_total",
            "total_descontos", "total_acrescimos",
        ):
            self.assertIn(campo, self.views)
            self.assertIn(campo, self.lista)

    def test_detalhe_exibe_itens_pagamentos_e_impressao(self):
        self.assertIn("Itens da venda", self.detalhe)
        self.assertIn("Pagamentos", self.detalhe)
        self.assertTrue(
            "Resumo financeiro" in self.detalhe
            or "detalhe_venda_resumo.html" in self.detalhe
        )
        self.assertTrue(
            "window.print()" in self.detalhe
            or "detalhe_venda_cabecalho.html" in self.detalhe
        )
        self.assertIn("motivo_cancelamento", self.detalhe)

    def test_sidebar_tem_historico_no_menu_pdv(self):
        self.assertIn("PDV-04E.3 - HISTORICO DE VENDAS", self.sidebar)
        self.assertIn("pdv:historico_vendas", self.sidebar)
        self.assertEqual(self.sidebar.count("Histórico de Vendas"), 1)

    def test_frente_caixa_nao_fica_ativa_no_historico(self):
        self.assertIn(
            "request.resolver_match.url_name == 'inicio'",
            self.sidebar,
        )

    def test_templates_tratam_relacionamentos_nulos(self):
        for template in (self.lista, self.detalhe):
            self.assertIn("{% if venda.vendedor %}", template)
            self.assertIn("{% if venda.operador %}", template)
            self.assertIn("{% if venda.cliente %}", template)
            self.assertIn("informado", template.lower())

        marcador_vendedor = "{% if venda.vendedor %}"
        acesso_vendedor = (
            "{{ venda.vendedor.get_full_name"
            "|default:venda.vendedor.username }}"
        )
        marcador_operador = "{% if venda.operador %}"
        acesso_operador = (
            "{{ venda.operador.get_full_name"
            "|default:venda.operador.username }}"
        )

        for template in (self.lista, self.detalhe):
            self.assertLess(
                template.index(marcador_vendedor),
                template.index(acesso_vendedor),
            )
            self.assertLess(
                template.index(marcador_operador),
                template.index(acesso_operador),
            )
