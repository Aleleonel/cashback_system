from pathlib import Path
from django.test import SimpleTestCase

class F24UiHttpVencimentoEscopoRedTests(SimpleTestCase):
    def setUp(self):
        self.view = Path("configuracoes/views.py").read_text(encoding="utf-8")
        self.template = Path("configuracoes/templates/configuracoes/comissoes.html").read_text(encoding="utf-8")

    def _bloco_provisionar(self):
        inicio = self.view.index('elif acao == "provisionar_comissao":')
        fim = self.view.index('elif acao == "fechamento_comissao":', inicio)
        return self.view[inicio:fim]

    def test_ui_deve_exigir_vencimento_explicito(self):
        self.assertIn('name="vencimento"', self.template)
        self.assertIn('type="date"', self.template)

    def test_view_nao_deve_inventar_vencimento_com_data_atual(self):
        bloco = self._bloco_provisionar()
        self.assertNotIn("vencimento=date.today()", bloco)
        self.assertIn('request.POST.get("vencimento")', bloco)

    def test_view_deve_validar_data_iso_sem_criar_titulo_em_entrada_invalida(self):
        bloco = self._bloco_provisionar()
        self.assertTrue("date.fromisoformat" in bloco or "parse_date" in bloco)
        self.assertIn("gerar_titulo_financeiro_comissao", bloco)

    def test_escopo_da_comissao_permanece_restrito_as_lojas_do_contexto(self):
        bloco = self._bloco_provisionar()
        self.assertIn("fechamento__loja__in=lojas", bloco)

    def test_link_titulo_deve_preservar_escopo_loja(self):
        self.assertIn("escopo=loja", self.template)
        self.assertIn("loja=", self.template)
        self.assertIn("comissao.titulo_financeiro.loja_id", self.template)

    def test_provisionamento_permanece_separado_da_baixa(self):
        bloco = self._bloco_provisionar()
        self.assertNotIn("registrar_baixa", bloco)
        self.assertNotIn("PERMISSAO_FINANCEIRO_BAIXAR", bloco)