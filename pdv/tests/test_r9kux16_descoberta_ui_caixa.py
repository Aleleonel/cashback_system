from pathlib import Path
from django.test import SimpleTestCase

class R9KUX16DescobertaUiCaixaTests(SimpleTestCase):
    def test_inicio_expoe_acoes_com_flags_granulares(self):
        t=Path("pdv/templates/pdv/inicio.html").read_text(encoding="utf-8")
        self.assertIn("pode_suprimento_caixa",t)
        self.assertIn("pdv:suprimento_caixa",t)
        self.assertIn("pode_sangria_caixa",t)
        self.assertIn("pdv:sangria_caixa",t)

    def test_contexto_inicio_calcula_permissoes_formais(self):
        v=Path("pdv/views.py").read_text(encoding="utf-8")
        self.assertIn('"pode_suprimento_caixa": usuario_tem_permissao(request.user, PERMISSAO_PDV_SUPRIMENTO)',v)
        self.assertIn('"pode_sangria_caixa": usuario_tem_permissao(request.user, PERMISSAO_PDV_SANGRIA)',v)