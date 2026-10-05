from pathlib import Path
from django.test import SimpleTestCase


class ComissoesGestaoMetasContractTests(SimpleTestCase):
    def setUp(self):
        root = Path(__file__).resolve().parents[2]
        self.views = (root / "configuracoes" / "views.py").read_text(encoding="utf-8")
        self.urls = (root / "configuracoes" / "urls.py").read_text(encoding="utf-8")
        self.template = (root / "configuracoes" / "templates" / "configuracoes" / "comissoes.html").read_text(encoding="utf-8")

    def test_existe_rota_e_view_para_editar_meta(self):
        self.assertIn("meta_comissao_editar", self.urls)
        self.assertIn("def meta_comissao_editar", self.views)

    def test_edicao_preserva_escopo_da_matriz_e_loja(self):
        self.assertIn("loja__matriz", self.views)

    def test_interface_expoe_acao_editar_meta(self):
        self.assertIn("meta_comissao_editar", self.template)
        self.assertIn("Editar", self.template)

    def test_interface_expoe_estado_ativo_inativo_sem_exclusao_fisica(self):
        self.assertIn("Ativa", self.template)
        self.assertIn("Inativa", self.template)
        self.assertNotIn("meta_comissao_excluir", self.template)
