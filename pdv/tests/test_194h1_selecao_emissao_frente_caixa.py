from pathlib import Path

from django.test import SimpleTestCase


class SelecaoEmissaoFrenteCaixa194H1Tests(SimpleTestCase):
    def setUp(self):
        self.raiz = Path(__file__).resolve().parents[2]

    def ler(self, relativo):
        return (self.raiz / relativo).read_text(encoding="utf-8")

    def test_modal_oferece_nao_fiscal_e_fiscal_nfce(self):
        template = self.ler("pdv/templates/pdv/inicio.html")
        self.assertIn('name="pdv-tipo-emissao" value="nao_fiscal" checked', template)
        self.assertIn('name="pdv-tipo-emissao" value="fiscal"', template)
        self.assertIn('id="pdv-uf-destino"', template)

    def test_front_transporta_tipo_emissao_e_uf_destino(self):
        javascript = self.ler("pdv/static/pdv/js/frente_caixa.js")
        self.assertIn("tipo_emissao: tipoEmissao", javascript)
        self.assertIn('uf_destino: tipoEmissao === "fiscal" ? ufDestino : ""', javascript)
        self.assertIn('tipoEmissao === "fiscal" && !ufDestino', javascript)

    def test_view_preserva_default_nao_fiscal_e_encaminha_uf(self):
        views = self.ler("pdv/views.py")
        self.assertIn('tipo_emissao=dados.get("tipo_emissao") or "nao_fiscal"', views)
        self.assertIn('uf_destino=dados.get("uf_destino") or ""', views)

    def test_service_persiste_contrato_antes_da_finalizacao(self):
        fechamento = self.ler("pdv/services/vendas/fechamento.py")
        self.assertIn('tipo_emissao="nao_fiscal"', fechamento)
        self.assertIn('venda.tipo_emissao = (tipo_emissao or "nao_fiscal").strip()', fechamento)
        self.assertIn('venda.uf_destino = (uf_destino or "").strip().upper()', fechamento)
        self.assertIn('"tipo_emissao", "uf_destino"', fechamento)
        self.assertLess(
            fechamento.index('venda.tipo_emissao = (tipo_emissao or "nao_fiscal").strip()'),
            fechamento.index('venda_finalizada = finalizar_venda('),
        )
