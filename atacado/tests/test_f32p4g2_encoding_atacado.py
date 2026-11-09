# F32P4G2 - Encoding regression for wholesale checkout UI.
from pathlib import Path
from django.test import SimpleTestCase


class F32P4G2EncodingAtacadoTests(SimpleTestCase):
    def test_template_sem_mojibake_e_utf8_valido(self):
        root = Path(__file__).resolve().parents[1]
        path = root / "templates" / "atacado" / "pedidos_lista.html"
        text = path.read_bytes().decode("utf-8-sig", errors="strict")
        for token in ("\u00e2\u20ac\u201d", "\u00c3\u00a2", "\ufffd"):
            self.assertNotIn(token, text)
        self.assertIn("\u2014", text)

    def test_resumo_e_caixa_sem_separadores_corrompidos(self):
        root = Path(__file__).resolve().parents[1]
        text = (root / "templates" / "atacado" / "pedidos_lista.html").read_text(encoding="utf-8-sig")
        self.assertIn("Caixa: {{ sessao_operacional.caixa.nome }} \u2014 {{ sessao_operacional.caixa.loja.nome }}", text)
        self.assertIn("pedido.id + ' \u2014 '", text)
