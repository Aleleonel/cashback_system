from pathlib import Path
from django.test import SimpleTestCase

class F24GeracaoTituloComissaoHardeningContractTests(SimpleTestCase):
    def test_servico_preserva_contrato_generico_financeiro(self):
        codigo = Path("configuracoes/services_comissoes.py").read_text(encoding="utf-8")
        self.assertIn("criar_titulo_financeiro(", codigo)
        self.assertNotIn("plano_conta=plano_conta", codigo)

    def test_identidade_financeira_e_estavel_por_snapshot(self):
        codigo = Path("configuracoes/services_comissoes.py").read_text(encoding="utf-8")
        self.assertIn('chave = f"COMISSAO:{comissao.pk}"', codigo)
        self.assertIn("origem_id=str(comissao.pk)", codigo)
        self.assertIn("OrigemTipo.COMISSAO", codigo)