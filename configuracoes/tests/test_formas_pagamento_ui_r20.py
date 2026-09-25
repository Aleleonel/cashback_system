from pathlib import Path

from django.test import SimpleTestCase


ROOT = Path(__file__).resolve().parents[2]


class FormasPagamentoUIR20ContractTests(SimpleTestCase):
    def test_catalogo_caixa_pagamentos_aponta_para_tela(self):
        texto = (ROOT / "configuracoes" / "catalogo.py").read_text(encoding="utf-8")
        self.assertIn("formas_pagamento", texto)
        self.assertRegex(texto, r"""url_name\s*=\s*['"][^'"]+['"]""")

    def test_urls_expoem_listagem_criacao_e_edicao(self):
        textos = []
        for arquivo in [
            ROOT / "configuracoes" / "urls.py",
            ROOT / "pdv" / "urls.py",
        ]:
            if arquivo.exists():
                textos.append(arquivo.read_text(encoding="utf-8"))
        texto = "\n".join(textos)
        self.assertIn("caixa-pagamentos/formas/", texto)
        self.assertRegex(texto, r"""name\s*=\s*['"][^'"]*forma[^'"]*pagamento[^'"]*['"]""")

    def test_view_referencia_modelo_e_acl_configuracoes(self):
        textos = []
        for base in [ROOT / "configuracoes", ROOT / "pdv"]:
            for arquivo in base.rglob("*.py"):
                if "migrations" not in arquivo.parts and "tests" not in arquivo.parts:
                    textos.append(arquivo.read_text(encoding="utf-8"))
        texto = "\n".join(textos)
        self.assertIn("FormaPagamento", texto)
        self.assertTrue(
            ("acessar_configuracoes" in texto)
            or ("configuracoes.acessar" in texto)
            or ("pode_acessar_configuracoes" in texto)
        )

    def test_template_expoe_flags_financeiras_com_ajuda(self):
        textos = []
        for base in [ROOT / "templates", ROOT / "configuracoes", ROOT / "pdv"]:
            if base.exists():
                for arquivo in base.rglob("*.html"):
                    textos.append(arquivo.read_text(encoding="utf-8"))
        texto = "\n".join(textos)
        self.assertIn("gera_contas_receber", texto)
        self.assertIn("movimenta_caixa", texto)
        self.assertTrue(
            ("Contas a Receber" in texto)
            or ("contas a receber" in texto)
        )

    def test_ui_nao_oferece_exclusao_fisica(self):
        textos = []
        for base in [ROOT / "configuracoes", ROOT / "pdv"]:
            for arquivo in base.rglob("*.py"):
                if "migrations" not in arquivo.parts and "tests" not in arquivo.parts:
                    textos.append(arquivo.read_text(encoding="utf-8"))
        texto = "\n".join(textos)
        self.assertNotRegex(
            texto,
            r"""FormaPagamento\.objects\.(?:filter\([^)]*\)\.)?delete\(""",
        )
class FormasPagamentoPlataformaContratoR20Tests(SimpleTestCase):
    def setUp(self):
        raiz=Path(__file__).resolve().parents[2]
        self.views=(raiz/"configuracoes"/"views.py").read_text(encoding="utf-8")
        self.lista=(raiz/"configuracoes"/"templates"/"configuracoes"/"formas_pagamento.html").read_text(encoding="utf-8")
    def test_superuser_exige_matriz_alvo_explicita(self):
        self.assertIn('request.GET.get("matriz"',self.views)
        self.assertIn('name="matriz"',self.lista)
        self.assertIn("Selecione uma matriz",self.lista)
    def test_nao_existe_fallback_primeira_matriz(self):
        self.assertNotIn(".first()",self.views)
        self.assertNotIn("matrizes[0]",self.views)
    def test_template_nao_contem_mojibake(self):
        self.assertNotIn("Ã",self.lista)
        self.assertNotIn("â†",self.lista)

class FormaPagamentoUsabilidadeH9GTests(SimpleTestCase):
    def setUp(self):
        raiz = Path(__file__).resolve().parents[2]
        self.forms = (raiz / "configuracoes" / "forms.py").read_text(encoding="utf-8")
        self.form_template = (raiz / "configuracoes" / "templates" / "configuracoes" / "forma_pagamento_form.html").read_text(encoding="utf-8")

    def test_labels_do_formulario_sem_mojibake(self):
        for texto in ("Código", "Máximo de parcelas", "Exige autorização", "Somente funcionário"):
            self.assertIn(texto, self.forms)
        for quebrado in ("CÃ³digo", "MÃ¡ximo", "autorizaÃ", "funcionÃ"):
            self.assertNotIn(quebrado, self.forms)

    def test_parcelamento_tem_controle_explicito_de_estado(self):
        self.assertIn('id_maximo_parcelas', self.form_template)
        self.assertIn('id_permite_parcelamento', self.form_template)
        self.assertIn('disabled', self.form_template)
        self.assertIn('value = "1"', self.form_template)

    def test_regras_financeiro_e_caixa_tem_ajuda_explicita(self):
        self.assertIn("form.gera_contas_receber", self.form_template)
        self.assertIn("form.movimenta_caixa", self.form_template)
        self.assertIn("controles independentes", self.form_template)