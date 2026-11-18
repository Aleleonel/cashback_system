from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from empresas.models import Matriz
from produtos.models.logistica import ModeloCaixaExpedicao, AuditoriaCadastroLogistico

class F33D2H11HTTPTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.ma = Matriz.objects.create(nome='F33H11 Matriz A')
        cls.mb = Matriz.objects.create(nome='F33H11 Matriz B')
        cls.ca = ModeloCaixaExpedicao.objects.create(matriz=cls.ma, nome='F33H11 A', largura_cm=10, altura_cm=10, comprimento_cm=10)
        cls.cb = ModeloCaixaExpedicao.objects.create(matriz=cls.mb, nome='F33H11 B', largura_cm=10, altura_cm=10, comprimento_cm=10)
        User=get_user_model()
        cls.admin=User.objects.create_superuser(username='f33h11_admin', email='f33h11@example.invalid', password='F33H11-Teste!')
        cls.operador=User.objects.create_user(username='f33h11_operador', password='F33H11-Teste!')

    def url(self, item):
        return reverse('produtos:logistica_acao', kwargs={'tipo':'caixas','item_id':item.pk})

    def test_01_anonimo_nao_exclui(self):
        r=self.client.post(self.url(self.ca), {'acao':'excluir'})
        self.assertIn(r.status_code,(302,401,403))
        self.assertTrue(ModeloCaixaExpedicao.objects.filter(pk=self.ca.pk).exists())

    def test_02_operador_sem_permissao_nao_exclui(self):
        self.client.force_login(self.operador)
        with patch('produtos.views.logistica.get_contexto_operacional_usuario',return_value={'matriz':self.ma}):
            r=self.client.post(self.url(self.ca), {'acao':'excluir'})
        self.assertNotEqual(r.status_code,500)
        self.assertTrue(ModeloCaixaExpedicao.objects.filter(pk=self.ca.pk).exists(), 'OPERADOR EXCLUIU SEM PERMISSAO')

    def test_03_superuser_nao_exclui_outra_matriz(self):
        self.client.force_login(self.admin)
        with patch('produtos.views.logistica.get_contexto_operacional_usuario',return_value={'matriz':self.ma}):
            r=self.client.post(self.url(self.cb), {'acao':'excluir'})
        self.assertEqual(r.status_code,404, 'Objeto de outra matriz deve retornar 404')
        self.assertTrue(ModeloCaixaExpedicao.objects.filter(pk=self.cb.pk).exists())

    def test_04_superuser_exclui_proprio_e_audita(self):
        self.client.force_login(self.admin)
        with patch('produtos.views.logistica.get_contexto_operacional_usuario',return_value={'matriz':self.ma}):
            r=self.client.post(self.url(self.ca), {'acao':'excluir'})
        self.assertEqual(r.status_code,302)
        self.assertFalse(ModeloCaixaExpedicao.objects.filter(pk=self.ca.pk).exists())
        self.assertTrue(AuditoriaCadastroLogistico.objects.filter(matriz=self.ma,usuario=self.admin,tipo='caixas',objeto_id=self.ca.pk,acao='EXCLUSAO').exists())

    def test_05_get_autenticado_nao_exclui(self):
        self.client.force_login(self.admin)
        with patch('produtos.views.logistica.get_contexto_operacional_usuario',return_value={'matriz':self.ma}):
            r=self.client.get(self.url(self.ca))
        self.assertEqual(r.status_code,405)
        self.assertTrue(ModeloCaixaExpedicao.objects.filter(pk=self.ca.pk).exists())
