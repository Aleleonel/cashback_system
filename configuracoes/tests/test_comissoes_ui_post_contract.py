from pathlib import Path
from django.test import SimpleTestCase

class ComissoesUIPostContractTests(SimpleTestCase):
    def setUp(self):
        self.views=Path("configuracoes/views.py").read_text(encoding="utf-8")
        self.tpl=Path("configuracoes/templates/configuracoes/comissoes.html").read_text(encoding="utf-8")
        i=self.views.index("def comissoes(request):")
        self.bloco=self.views[i:i+7000]

    def test_post_politica_matriz_tem_acao_validacao_e_save(self):
        self.assertIn('request.method == "POST"',self.bloco)
        self.assertIn('"salvar_configuracao"',self.bloco)
        self.assertIn("ConfiguracaoComissaoMatrizForm(request.POST",self.bloco)
        self.assertIn(".is_valid()",self.bloco)
        self.assertIn(".save()",self.bloco)

    def test_post_meta_valida_loja_no_escopo(self):
        self.assertIn('"adicionar_meta"',self.bloco)
        self.assertIn("loja_id",self.bloco)
        self.assertIn("lojas.get",self.bloco)
        self.assertIn("MetaComissaoLojaForm(request.POST",self.bloco)

    def test_template_habilita_acoes_post(self):
        self.assertIn('value="salvar_configuracao"',self.tpl)
        self.assertIn('value="adicionar_meta"',self.tpl)
        self.assertNotIn('type="submit" class="btn btn-primary mt-3" disabled',self.tpl)