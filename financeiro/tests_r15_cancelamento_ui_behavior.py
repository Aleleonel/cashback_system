from pathlib import Path
from django.test import SimpleTestCase


class R15CancelamentoTituloUIBehaviorTests(SimpleTestCase):
    def setUp(self):
        self.views = Path("financeiro/views.py").read_text(encoding="utf-8")
        self.template = Path("financeiro/templates/financeiro/titulo_cancelar_confirm.html").read_text(encoding="utf-8")
        self.detail = Path("financeiro/templates/financeiro/titulo_detalhe.html").read_text(encoding="utf-8")

    def test_get_nao_invoca_servico_fora_do_bloco_post(self):
        self.assertIn('if request.method == "POST":', self.views)
        post_pos = self.views.index('if request.method == "POST":', self.views.index("def titulo_cancelar("))
        service_pos = self.views.index("cancelar_titulo_financeiro(", post_pos)
        render_pos = self.views.index('return render(', service_pos)
        self.assertLess(post_pos, service_pos)
        self.assertLess(service_pos, render_pos)

    def test_view_restringe_titulo_ao_mesmo_escopo_do_detalhe(self):
        start = self.views.index("def titulo_cancelar(")
        end = self.views.index("\ndef ", start + 5)
        block = self.views[start:end]
        self.assertIn("_resolver_escopo(request, matriz)", block)
        self.assertIn("TituloFinanceiro.objects.filter(matriz=matriz)", block)
        self.assertIn("ESCOPO_MATRIZ", block)
        self.assertIn("loja__isnull=True", block)
        self.assertIn("ESCOPO_LOJA", block)
        self.assertIn("queryset.filter(loja=loja)", block)

    def test_erro_de_dominio_permanece_na_confirmacao(self):
        start = self.views.index("def titulo_cancelar(")
        end = self.views.index("\ndef ", start + 5)
        block = self.views[start:end]
        self.assertIn("except ValidationError as exc:", block)
        self.assertIn('"erro": erro', block)
        self.assertIn("{% if erro %}", self.template)

    def test_sucesso_redireciona_para_detalhe(self):
        start = self.views.index("def titulo_cancelar(")
        end = self.views.index("\ndef ", start + 5)
        block = self.views[start:end]
        self.assertIn('reverse("financeiro:titulo_detalhe"', block)
        self.assertIn('return redirect(f"{detalhe_url}?{query_escopo}")', block)

    def test_confirmacao_exige_csrf_e_post(self):
        self.assertIn('method="post"', self.template)
        self.assertIn("{% csrf_token %}", self.template)
        self.assertIn("Confirmar cancelamento", self.template)

    def test_detalhe_nao_oferece_cancelar_quando_status_cancelado(self):
        self.assertIn('{% if titulo.status != "CANCELADO" %}', self.detail)
        self.assertIn("financeiro:titulo_cancelar", self.detail)