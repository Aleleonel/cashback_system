from pathlib import Path
from django.test import SimpleTestCase
from accounts.permissions import PERMISSAO_FINANCEIRO_REABRIR_COMPETENCIA, PERMISSOES_FINANCEIRO

class F26Z58PermissaoReaberturaTests(SimpleTestCase):
    def test_capability_existe(self):
        self.assertEqual(PERMISSAO_FINANCEIRO_REABRIR_COMPETENCIA, 'financeiro.reabrir_competencia')
        self.assertIn(PERMISSAO_FINANCEIRO_REABRIR_COMPETENCIA, PERMISSOES_FINANCEIRO)
    def test_view_exige_capability_especifica(self):
        x=Path('financeiro/views.py').read_text(encoding='utf-8'); i=x.index('def fechamento_gerencial_reabrir'); self.assertIn('@require_permission(PERMISSAO_FINANCEIRO_REABRIR_COMPETENCIA)',x[max(0,i-180):i])
    def test_service_defesa_em_profundidade(self):
        x=Path('financeiro/services.py').read_text(encoding='utf-8'); i=x.index('def reabrir_competencia_gerencial'); b=x[i:i+900]; self.assertIn('usuario_tem_permissao(usuario, PERMISSAO_FINANCEIRO_REABRIR_COMPETENCIA)',b); self.assertIn('PermissionDenied',b)
