from pathlib import Path

from django.test import SimpleTestCase


class CancelarVendaResgateTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        root = Path(__file__).resolve().parents[2]

        cls.template = (
            root / "pdv" / "templates" / "pdv" / "inicio.html"
        ).read_text(encoding="utf-8-sig")

        cls.rescue = (
            root
            / "pdv"
            / "static"
            / "pdv"
            / "js"
            / "cancelar_venda_resgate.js"
        ).read_text(encoding="utf-8-sig")

        cls.main_js = (
            root / "pdv" / "static" / "pdv" / "js" / "frente_caixa.js"
        ).read_text(encoding="utf-8-sig")

        cls.views = (
            root / "pdv" / "views.py"
        ).read_text(encoding="utf-8-sig")

        cls.urls = (
            root / "pdv" / "urls.py"
        ).read_text(encoding="utf-8-sig")

        cls.fechamento = (
            root / "pdv" / "services" / "vendas" / "fechamento.py"
        ).read_text(encoding="utf-8-sig")

        cls.beneficios = (
            root / "pdv" / "services" / "vendas" / "beneficios.py"
        ).read_text(encoding="utf-8-sig")

        cls.utilizacao = (
            root / "vouchers" / "services" / "utilizacao.py"
        ).read_text(encoding="utf-8-sig")

    def test_resgate_carregado_uma_vez(self):
        self.assertEqual(
            self.template.count("cancelar_venda_resgate.js"),
            1,
        )

    def test_resgate_carrega_depois_da_frente_caixa(self):
        self.assertLess(
            self.template.index("frente_caixa.js"),
            self.template.index("cancelar_venda_resgate.js"),
        )

    def test_intercepta_apenas_cancelar_venda(self):
        self.assertIn(
            'document.getElementById("pdv-cancelar-venda")',
            self.rescue,
        )
        self.assertIn("event.stopImmediatePropagation();", self.rescue)
        self.assertIn("true\n    );", self.rescue)

    def test_chama_url_e_recarrega_tela(self):
        self.assertIn("app.dataset.cancelarVendaUrl", self.rescue)
        self.assertIn('method: "POST"', self.rescue)
        self.assertIn('"X-CSRFToken": token', self.rescue)
        self.assertIn(
            'body.set("csrfmiddlewaretoken", token)',
            self.rescue,
        )
        self.assertIn(
            'input[name="csrfmiddlewaretoken"]',
            self.rescue,
        )
        self.assertIn("window.location.reload();", self.rescue)

    def test_backend_cancelamento_permanece(self):
        self.assertIn(
            "def cancelar_venda_web",
            self.views,
        )
        self.assertIn(
            "name='cancelar_venda'",
            self.urls,
        )

    def test_pagamento_misto_permanece(self):
        self.assertIn(
            "const resumoPagamentos = () => {",
            self.main_js,
        )
        self.assertIn(
            "const atualizarLinha = (linha, origem = null) => {",
            self.main_js,
        )
        self.assertIn(
            "def _registrar_pagamentos(",
            self.fechamento,
        )

    def test_voucher_permanece_por_delegacao(self):
        self.assertIn(
            "resolver_beneficio_da_venda(",
            self.fechamento,
        )
        self.assertIn(
            "registrar_uso_voucher(",
            self.beneficios,
        )
        self.assertIn(
            "UsoVoucher.objects.create(",
            self.utilizacao,
        )
        self.assertIn(
            "voucher_bloqueado.total_utilizado >= voucher_bloqueado.limite_utilizacao",
            self.utilizacao,
        )