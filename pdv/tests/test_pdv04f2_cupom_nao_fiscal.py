from pathlib import Path
from django.template.loader import get_template
from django.test import SimpleTestCase
from django.urls import reverse


class Pdv04F2CupomNaoFiscalContratoTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.views = Path("pdv/views.py").read_text(encoding="utf-8")
        cls.urls = Path("pdv/urls.py").read_text(encoding="utf-8")
        cls.cupom = Path("pdv/templates/pdv/cupom_venda_80mm.html").read_text(encoding="utf-8")
        cls.cabecalho = Path("pdv/templates/pdv/partials/detalhe_venda_cabecalho.html").read_text(encoding="utf-8")
        cls.historico = Path("pdv/templates/pdv/historico_vendas.html").read_text(encoding="utf-8")

    def test_rota(self):
        self.assertIn('name="cupom_venda_nao_fiscal"', self.urls)
        self.assertIn("/cupom/", reverse("pdv:cupom_venda_nao_fiscal", args=["00000000-0000-0000-0000-000000000001"]))

    def test_view_protegida(self):
        self.assertIn("def cupom_venda_nao_fiscal(request, venda_uuid):", self.views)
        self.assertIn("@require_permission(PERMISSAO_PDV_VISUALIZAR)", self.views)
        self.assertIn("loja__in=lojas", self.views)

    def test_template(self):
        self.assertIsNotNone(get_template("pdv/cupom_venda_80mm.html"))
        self.assertIn("DOCUMENTO NÃO FISCAL", self.cupom)
        self.assertIn("size:80mm auto", self.cupom)
        self.assertIn("window.print()", self.cupom)

    def test_dados(self):
        for item in ("venda.loja.nome", "venda.numero", "item.produto.nome", "pagamento.forma_pagamento.nome", "venda.total"):
            self.assertIn(item, self.cupom)

    def test_acessos(self):
        self.assertIn("pdv:cupom_venda_nao_fiscal", self.cabecalho)
        self.assertIn("pdv:cupom_venda_nao_fiscal", self.historico)
        self.assertIn("Imprimir cupom", self.cabecalho)
        self.assertIn("Reimprimir", self.historico)
