from pathlib import Path
from django.test import SimpleTestCase

ROOT = Path(__file__).resolve().parents[2]
VIEWS = (ROOT / "configuracoes" / "views.py").read_text(encoding="utf-8")
TEMPLATE = (ROOT / "configuracoes" / "templates" / "configuracoes" / "comissoes.html").read_text(encoding="utf-8")

class ComissoesUICorretivoContractTests(SimpleTestCase):
    def test_get_nao_pode_usar_get_or_create(self):
        inicio = VIEWS.index("def comissoes(")
        fim = VIEWS.index("\ndef regras_comerciais(", inicio)
        bloco = VIEWS[inicio:fim]
        self.assertNotIn("ConfiguracaoComissaoMatriz.objects.get_or_create", bloco)

    def test_plataforma_deve_ter_selecao_explicita_de_matriz(self):
        self.assertIn("matrizes_plataforma", VIEWS)
        self.assertIn('request.GET.get("matriz"', VIEWS)
        self.assertIn('name="matriz"', TEMPLATE)

    def test_redirect_post_deve_preservar_matriz_selecionada(self):
        inicio = VIEWS.index("def comissoes(")
        fim = VIEWS.index("\ndef regras_comerciais(", inicio)
        bloco = VIEWS[inicio:fim]
        self.assertIn("matriz=", bloco)

    def test_post_loja_deve_continuar_limitado_ao_contexto(self):
        inicio = VIEWS.index("def comissoes(")
        fim = VIEWS.index("\ndef regras_comerciais(", inicio)
        bloco = VIEWS[inicio:fim]
        self.assertIn("lojas.get(pk=loja_id)", bloco)