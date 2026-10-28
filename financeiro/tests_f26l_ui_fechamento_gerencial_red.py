from pathlib import Path
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import NoReverseMatch, reverse
from empresas.models import Matriz

User=get_user_model()

class F26LUIFechamentoGerencialContratoRedTests(TestCase):
    def setUp(self):
        self.m1=Matriz.objects.create(nome="F26L Matriz 1")
        self.m2=Matriz.objects.create(nome="F26L Matriz 2")
        self.super=User.objects.create_user(username="f26l_super",password="x",is_superuser=True,is_staff=True)
        self.admin=User.objects.create_user(username="f26l_admin",password="x",perfil=User.PERFIL_ADMIN_LOJA,matriz=self.m1)
        self.oper=User.objects.create_user(username="f26l_oper",password="x",perfil=User.PERFIL_OPERADOR,matriz=self.m1)

    def _url(self, name, **kw):
        try:return reverse(name,kwargs=kw or None)
        except NoReverseMatch as exc:self.fail(f"rota ausente {name}: {exc}")

    def test_01_rota_tela_existe(self):
        self._url("financeiro:fechamento_gerencial")

    def test_02_superuser_sem_matriz_recebe_tela_de_selecao_explicita(self):
        self.client.force_login(self.super)
        r=self.client.get(self._url("financeiro:fechamento_gerencial"))
        self.assertEqual(r.status_code,200)
        self.assertContains(r,"Selecione uma matriz")

    def test_03_superuser_pode_selecionar_matriz_explicitamente(self):
        self.client.force_login(self.super)
        r=self.client.get(self._url("financeiro:fechamento_gerencial")+f"?matriz={self.m1.pk}&ano=2026&mes=10")
        self.assertEqual(r.status_code,200)
        self.assertEqual(getattr(r.context.get("matriz"),"pk",None),self.m1.pk)

    def test_04_admin_fica_restrito_a_propria_matriz(self):
        self.client.force_login(self.admin)
        r=self.client.get(self._url("financeiro:fechamento_gerencial")+f"?matriz={self.m2.pk}&ano=2026&mes=10")
        self.assertEqual(r.status_code,200)
        self.assertEqual(getattr(r.context.get("matriz"),"pk",None),self.m1.pk)

    def test_05_operador_nao_acessa_fechamento(self):
        self.client.force_login(self.oper)
        r=self.client.get(self._url("financeiro:fechamento_gerencial"))
        self.assertEqual(r.status_code,403)

    def test_06_tela_expoe_checklist_e_estado(self):
        self.client.force_login(self.super)
        r=self.client.get(self._url("financeiro:fechamento_gerencial")+f"?matriz={self.m1.pk}&ano=2026&mes=10")
        self.assertEqual(r.status_code,200)
        self.assertIn("checklist",r.context)
        self.assertIn("fechamento",r.context)
        self.assertContains(r,"Checklist")

    def test_07_rotas_post_fechar_e_reabrir_existem(self):
        self._url("financeiro:fechamento_gerencial_fechar")
        self._url("financeiro:fechamento_gerencial_reabrir")

    def test_08_template_tem_confirmacao_profissional_e_motivo_reabertura(self):
        p=Path(__file__).resolve().parent/"templates"/"financeiro"/"fechamento_gerencial.html"
        self.assertTrue(p.exists(),"template fechamento_gerencial.html ausente")
        txt=p.read_text(encoding="utf-8")
        self.assertIn("modal",txt.lower())
        self.assertIn("csrf_token",txt)
        self.assertIn("motivo",txt.lower())
        self.assertNotIn("window.confirm",txt)

    def test_09_sidebar_financeiro_expoe_acesso_e_relatorios_nao_duplica(self):
        raiz=Path(__file__).resolve().parents[1]
        sidebar=(raiz/"templates"/"partials"/"sidebar.html").read_text(encoding="utf-8")
        hub=(raiz/"relatorios"/"templates"/"relatorios"/"financeiro.html").read_text(encoding="utf-8")
        self.assertIn("financeiro:fechamento_gerencial",sidebar)
        self.assertIn("Fechamento Gerencial",sidebar)
        self.assertNotIn("financeiro:fechamento_gerencial",hub)
        self.assertNotIn("Fechamento Gerencial",hub)
