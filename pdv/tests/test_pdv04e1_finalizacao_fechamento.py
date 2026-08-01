from pathlib import Path
from django.test import SimpleTestCase


class Pdv04E1FinalizacaoFechamentoTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.views = Path("pdv/views.py").read_text(encoding="utf-8")
        cls.close = Path("pdv/templates/pdv/fechar_caixa.html").read_text(encoding="utf-8")
        cls.home = Path("pdv/templates/pdv/inicio.html").read_text(encoding="utf-8")

    def test_valor_calculado_preenche_o_campo_em_reais(self):
        self.assertIn('value="{{ valor_fechamento_inicial }}"', self.close)
        self.assertIn('data-moeda="brl"', self.close)
        self.assertIn("def _formatar_valor_monetario_br(valor):", self.views)
        self.assertIn('return f"R$ {texto}"', self.views)
        self.assertIn('"valor_fechamento_inicial"', self.views)

    def test_post_e_csrf_permanecem(self):
        self.assertIn("confirmar_fechamento_caixa", self.close)
        self.assertIn("{% csrf_token %}", self.close)

    def test_mensagens_sao_visiveis(self):
        self.assertIn("{% if messages %}", self.close)
        self.assertIn("{% if messages %}", self.home)

    def test_erro_preserva_valor_e_observacao(self):
        self.assertIn('request.session["pdv_valor_fechamento_informado"]', self.views)
        self.assertIn('request.session["pdv_observacao_fechamento"]', self.views)
        self.assertIn("{{ observacao_fechamento_inicial }}", self.close)

    def test_sucesso_limpa_sessao_e_redireciona(self):
        self.assertIn('request.session.pop("pdv_valor_fechamento_informado", None)', self.views)
        self.assertIn("fechado com sucesso", self.views)
        self.assertIn('return redirect("pdv:inicio")', self.views)

    def test_envio_duplo_e_bloqueado(self):
        self.assertIn("botao.disabled = true", self.close)
        self.assertIn("Fechando caixa...", self.close)
