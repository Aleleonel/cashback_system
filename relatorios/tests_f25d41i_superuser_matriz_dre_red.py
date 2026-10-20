from pathlib import Path
from django.test import SimpleTestCase

class DRESuperuserMatrizContratoREDTests(SimpleTestCase):
    def setUp(self):
        raiz=Path(__file__).resolve().parents[1]
        self.views=(raiz/"relatorios"/"views.py").read_text(encoding="utf-8")
        self.tpl=(raiz/"relatorios"/"templates"/"relatorios"/"dre.html").read_text(encoding="utf-8")

    def test_superuser_nao_usa_contexto_operacional(self):
        trecho=self.views[self.views.index("def _contexto_dre"):self.views.index("@login_required",self.views.index("def _contexto_dre"))]
        self.assertIn("if request.user.is_superuser",trecho)
        ramo_superuser=trecho.split("if request.user.is_superuser:",1)[1].split("else:",1)[0]
        self.assertNotIn("get_contexto_operacional_usuario",ramo_superuser)
        self.assertIn("get_contexto_operacional_usuario(request.user)",trecho.split("else:",1)[1])

    def test_superuser_exige_matriz_alvo_explicita(self):
        self.assertIn('request.GET.get("matriz"',self.views)
        self.assertIn('name="matriz"',self.tpl)

    def test_superuser_nao_escolhe_primeira_matriz_implicitamente(self):
        trecho=self.views[self.views.index("def _contexto_dre"):self.views.index("@login_required",self.views.index("def _contexto_dre"))]
        self.assertNotIn("Matriz.objects.first()",trecho)
        self.assertNotIn("matrizes.first()",trecho)

    def test_fabricaadm_mantem_contexto_operacional_da_propria_matriz(self):
        trecho=self.views[self.views.index("def _contexto_dre"):self.views.index("@login_required",self.views.index("def _contexto_dre"))]
        self.assertIn("get_contexto_operacional_usuario(request.user)",trecho)

    def test_superuser_expoe_lista_de_matrizes_para_selecao(self):
        trecho=self.views[self.views.index("def _contexto_dre"):self.views.index("@login_required",self.views.index("def _contexto_dre"))]
        self.assertIn("Matriz.objects",trecho)
        self.assertIn('"matrizes"',trecho)

    def test_matriz_query_nao_pode_afetar_usuario_nao_superuser(self):
        trecho=self.views[self.views.index("def _contexto_dre"):self.views.index("@login_required",self.views.index("def _contexto_dre"))]
        self.assertIn("if request.user.is_superuser",trecho)
        self.assertIn("else:",trecho)