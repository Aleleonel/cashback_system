from pathlib import Path
from django.test import SimpleTestCase

class F24UiProvisionamentoPermissaoRedTests(SimpleTestCase):
    """
    Provisionar cria obrigacao financeira; portanto exige permissao financeira
    explicita. A baixa continua separada em financeiro.baixar.
    """

    def test_provisionamento_deve_exigir_permissao_financeira_lancar_despesa(self):
        fonte = Path("configuracoes/views.py").read_text(encoding="utf-8")
        self.assertIn("PERMISSAO_FINANCEIRO_LANCAR_DESPESA", fonte)
        inicio = fonte.index('elif acao == "provisionar_comissao":')
        fim = fonte.index('elif acao == "fechamento_comissao":', inicio)
        bloco = fonte[inicio:fim]
        self.assertIn("usuario_tem_permissao", bloco)
        self.assertIn("PERMISSAO_FINANCEIRO_LANCAR_DESPESA", bloco)

    def test_provisionamento_nao_deve_usar_permissao_de_baixa(self):
        fonte = Path("configuracoes/views.py").read_text(encoding="utf-8")
        inicio = fonte.index('elif acao == "provisionar_comissao":')
        fim = fonte.index('elif acao == "fechamento_comissao":', inicio)
        bloco = fonte[inicio:fim]
        self.assertNotIn("PERMISSAO_FINANCEIRO_BAIXAR", bloco)

    def test_template_deve_ocultar_provisionar_sem_flag_de_permissao(self):
        template = Path("configuracoes/templates/configuracoes/comissoes.html").read_text(encoding="utf-8")
        self.assertIn("pode_provisionar_comissao", template)
        self.assertIn("pode_provisionar_comissao and comissao.elegivel", template)

    def test_escopo_deve_continuar_resolvido_pelo_fechamento_e_lojas(self):
        fonte = Path("configuracoes/views.py").read_text(encoding="utf-8")
        inicio = fonte.index('elif acao == "provisionar_comissao":')
        fim = fonte.index('elif acao == "fechamento_comissao":', inicio)
        bloco = fonte[inicio:fim]
        self.assertIn("fechamento__loja__in=lojas", bloco)