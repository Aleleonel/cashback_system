from pathlib import Path
from django.test import SimpleTestCase

class ComissoesUIOperacionalContractTests(SimpleTestCase):
    def test_forms_expoem_configuracao_matriz_e_meta_loja(self):
        src=Path("configuracoes/forms.py").read_text(encoding="utf-8")
        self.assertIn("ConfiguracaoComissaoMatrizForm",src)
        self.assertIn("MetaComissaoLojaForm",src)
        self.assertIn("exigir_minimo_individual",src)
        self.assertIn("minimo_vendas_vendedor",src)
        self.assertIn("valor_meta",src)
        self.assertIn("percentual_comissao",src)

    def test_view_comissoes_carrega_configuracao_e_lojas_do_escopo(self):
        src=Path("configuracoes/views.py").read_text(encoding="utf-8")
        inicio=src.index("def comissoes(request):")
        bloco=src[inicio:inicio+5000]
        self.assertIn("ConfiguracaoComissaoMatriz",bloco)
        self.assertIn("MetaComissaoLoja",bloco)
        self.assertIn("lojas",bloco)
        self.assertIn("matriz",bloco)

    def test_template_tem_formulario_operacional_e_csrf(self):
        txt=Path("configuracoes/templates/configuracoes/comissoes.html").read_text(encoding="utf-8")
        self.assertIn('<form',txt)
        self.assertIn("{% csrf_token %}",txt)
        self.assertIn("exigir_minimo_individual",txt)
        self.assertIn("minimo_vendas_vendedor",txt)
        self.assertIn("valor_meta",txt)
        self.assertIn("percentual_comissao",txt)