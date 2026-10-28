from pathlib import Path
from django.test import SimpleTestCase
from accounts import permissions

class F26Z8CapabilitiesFinanceiroRED(SimpleTestCase):
    def setUp(self):
        raiz=Path(__file__).resolve().parents[1]
        self.p=(raiz/"accounts"/"permissions.py").read_text(encoding="utf-8")
        self.v=(raiz/"financeiro"/"views.py").read_text(encoding="utf-8")

    def test_01_existe_capability_editar_lancamento(self):
        self.assertEqual(permissions.PERMISSAO_FINANCEIRO_EDITAR_LANCAMENTO,"financeiro.editar_lancamento")

    def test_02_existe_capability_cancelar_lancamento(self):
        self.assertEqual(permissions.PERMISSAO_FINANCEIRO_CANCELAR_LANCAMENTO,"financeiro.cancelar_lancamento")

    def test_03_capabilities_constam_catalogo_financeiro(self):
        self.assertIn(permissions.PERMISSAO_FINANCEIRO_EDITAR_LANCAMENTO,permissions.PERMISSOES_FINANCEIRO)
        self.assertIn(permissions.PERMISSAO_FINANCEIRO_CANCELAR_LANCAMENTO,permissions.PERMISSOES_FINANCEIRO)

    def test_04_capabilities_constam_catalogo_ui_permissoes(self):
        self.assertIn("financeiro.editar_lancamento",self.p)
        self.assertIn("financeiro.cancelar_lancamento",self.p)

    def test_05_cancelamento_nao_pode_ser_protegido_apenas_por_visualizar(self):
        pos=self.v.index("def titulo_cancelar")
        inicio=self.v.rfind("@require_permission",0,pos)
        bloco=self.v[inicio:pos]
        self.assertIn("PERMISSAO_FINANCEIRO_CANCELAR_LANCAMENTO",bloco)
        self.assertNotIn("PERMISSAO_FINANCEIRO_VISUALIZAR",bloco)

    def test_06_editar_cancelar_sao_independentes_das_permissoes_existentes(self):
        novas={permissions.PERMISSAO_FINANCEIRO_EDITAR_LANCAMENTO,permissions.PERMISSAO_FINANCEIRO_CANCELAR_LANCAMENTO}
        antigas={permissions.PERMISSAO_FINANCEIRO_BAIXAR,permissions.PERMISSAO_FINANCEIRO_GERENCIAR,permissions.PERMISSAO_FINANCEIRO_LANCAR_DESPESA}
        self.assertTrue(novas.isdisjoint(antigas))
        self.assertEqual(len(novas),2)

    def test_07_operador_nao_recebe_novas_capabilities_por_padrao(self):
        # O contrato exige capacidade explícita, não concessão implícita por perfil.
        for codigo in ("financeiro.editar_lancamento","financeiro.cancelar_lancamento"):
            self.assertNotRegex(self.p,rf"PERFIL_OPERADOR[\s\S]{{0,400}}{codigo.replace('.', r'\.')}")

    def test_08_fechamento_reabertura_nao_dependem_das_novas_capabilities(self):
        trecho=self.v[self.v.index("def fechamento_gerencial"):]
        self.assertNotIn("PERMISSAO_FINANCEIRO_EDITAR_LANCAMENTO",trecho)
        self.assertNotIn("PERMISSAO_FINANCEIRO_CANCELAR_LANCAMENTO",trecho)
