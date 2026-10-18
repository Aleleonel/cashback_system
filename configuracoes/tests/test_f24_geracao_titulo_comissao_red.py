from pathlib import Path
from django.test import SimpleTestCase


class F24GeracaoTituloComissaoRedTests(SimpleTestCase):
    def test_servico_expoe_geracao_financeira_por_snapshot(self):
        p = Path("configuracoes/services_comissoes.py")
        codigo = p.read_text(encoding="utf-8")
        self.assertIn(
            "gerar_titulo_financeiro_comissao",
            codigo,
            "F24 exige servico explicito para converter snapshot em obrigacao financeira.",
        )

    def test_servico_usa_origem_comissao_e_idempotencia_estavel(self):
        codigo = Path("configuracoes/services_comissoes.py").read_text(encoding="utf-8")
        self.assertIn("OrigemTipo.COMISSAO", codigo)
        self.assertIn("chave_idempotencia", codigo)
        self.assertIn("ComissaoVendedor", codigo)