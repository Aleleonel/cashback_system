from pathlib import Path
from django.test import SimpleTestCase

class ComissoesUIFechamentoHistoricoContractTests(SimpleTestCase):
    def setUp(self):
        root=Path(__file__).resolve().parents[2]
        self.views=(root/"configuracoes"/"views.py").read_text(encoding="utf-8")
        self.urls=(root/"configuracoes"/"urls.py").read_text(encoding="utf-8")
        self.template=(root/"configuracoes"/"templates"/"configuracoes"/"comissoes.html").read_text(encoding="utf-8")

    def test_view_expoe_fechamento_mensal_operacional(self):
        self.assertIn("fechar_comissoes_competencia", self.views)
        self.assertIn("fechamento_comissao", self.views)

    def test_post_fechamento_exige_loja_ano_mes(self):
        self.assertIn('request.POST.get("loja_fechamento_id")', self.views)
        self.assertIn('request.POST.get("competencia_ano")', self.views)
        self.assertIn('request.POST.get("competencia_mes")', self.views)

    def test_interface_expoe_controles_de_fechamento(self):
        self.assertIn("loja_fechamento_id", self.template)
        self.assertIn("competencia_ano", self.template)
        self.assertIn("competencia_mes", self.template)
        self.assertIn("Fechar comissões", self.template)
        self.assertNotIn("Fechamento ainda não disponível", self.template)

    def test_interface_expoe_historico_immutavel_e_detalhamento(self):
        self.assertIn("Histórico de fechamentos", self.template)
        self.assertIn("fechamentos_comissao", self.views)
        self.assertIn("comissoes_vendedores", self.template)

    def test_nao_expoe_exclusao_ou_recalculo_de_fechamento(self):
        self.assertNotIn("excluir_fechamento_comissao", self.urls)
        self.assertNotIn("recalcular_fechamento_comissao", self.urls)
        self.assertNotIn("Excluir fechamento", self.template)
        self.assertNotIn("Recalcular fechamento", self.template)