from pathlib import Path
from django.test import SimpleTestCase


class R15CancelamentoTituloUIRedTests(SimpleTestCase):
    def test_rota_cancelamento_deve_existir(self):
        urls = Path("financeiro/urls.py").read_text(encoding="utf-8")
        self.assertIn('name="titulo_cancelar"', urls)

    def test_view_cancelamento_deve_exigir_permissao_baixar_e_usar_servico(self):
        views = Path("financeiro/views.py").read_text(encoding="utf-8")
        self.assertIn("def titulo_cancelar(", views)
        self.assertIn("@require_permission(PERMISSAO_FINANCEIRO_BAIXAR)", views)
        self.assertIn("cancelar_titulo_financeiro(", views)

    def test_detalhe_deve_oferecer_cancelamento_quando_titulo_nao_cancelado(self):
        template = Path("financeiro/templates/financeiro/titulo_detalhe.html").read_text(encoding="utf-8")
        self.assertIn("financeiro:titulo_cancelar", template)
        self.assertIn("Cancelar título", template)

    def test_template_confirmacao_deve_existir_com_post(self):
        path = Path("financeiro/templates/financeiro/titulo_cancelar_confirm.html")
        self.assertTrue(path.exists())
        if path.exists():
            template = path.read_text(encoding="utf-8")
            self.assertIn('method="post"', template)
            self.assertIn("Confirmar cancelamento", template)