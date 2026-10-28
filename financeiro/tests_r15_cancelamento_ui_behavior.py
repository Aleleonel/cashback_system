from pathlib import Path
from django.test import SimpleTestCase


class R15CancelamentoTituloUIBehaviorTests(SimpleTestCase):
    def setUp(self):
        self.views = Path("financeiro/views.py").read_text(encoding="utf-8")
        self.template = Path("financeiro/templates/financeiro/titulo_cancelar_confirm.html").read_text(encoding="utf-8")
        self.detail = Path("financeiro/templates/financeiro/titulo_detalhe.html").read_text(encoding="utf-8")

    def test_get_nao_invoca_servico_fora_do_bloco_post(self):
        start = self.views.index("def titulo_cancelar")
        end = self.views.index("@login_required", start)
        bloco = self.views[start:end]
        form_pos = bloco.index("CancelarTituloForm(")
        post_pos = bloco.index('if request.method == "POST" and form.is_valid():', form_pos)
        service_pos = bloco.index("cancelar_titulo_financeiro(", post_pos)
        self.assertGreater(service_pos, post_pos)
        self.assertNotIn("cancelar_titulo_financeiro(", bloco[form_pos:post_pos])


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
        self.assertIn("form.add_error(None, mensagem)", block)
        self.assertIn('"form": form', block)
        self.assertIn("{% if form.non_field_errors %}", self.template)

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
        self.assertIn("{% if pode_cancelar_titulo %}", self.detail)
        self.assertIn("financeiro:titulo_cancelar", self.detail)