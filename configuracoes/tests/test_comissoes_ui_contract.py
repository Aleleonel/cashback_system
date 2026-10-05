from pathlib import Path
from django.test import SimpleTestCase
from django.urls import NoReverseMatch, reverse

class ComissoesUIContractTests(SimpleTestCase):
    def test_hub_disponibiliza_comissoes(self):
        src=Path("configuracoes/views.py").read_text(encoding="utf-8")
        bloco=src[src.index('"titulo": "Comissões"'):]
        self.assertIn('"url_name": "configuracoes:comissoes"', bloco[:500])
        self.assertIn('"disponivel": True', bloco[:500])

    def test_rota_principal_comissoes_existe(self):
        try:
            url=reverse("configuracoes:comissoes")
        except NoReverseMatch:
            self.fail("Rota configuracoes:comissoes ainda não existe.")
        self.assertIn("comisso", url)

    def test_template_principal_comissoes_existe(self):
        self.assertTrue(Path("configuracoes/templates/configuracoes/comissoes.html").exists())

    def test_ui_preve_configuracao_matriz_metas_loja_e_fechamento(self):
        p=Path("configuracoes/templates/configuracoes/comissoes.html")
        if not p.exists():
            self.fail("Template principal de comissões ainda não existe.")
        txt=p.read_text(encoding="utf-8")
        for trecho in ("Elegibilidade", "Mínimo", "Metas", "Percentual", "Competência", "Fechar comissões"):
            self.assertIn(trecho,txt)