from django.test import TestCase
from django.urls import NoReverseMatch, reverse
from accounts.models import Usuario
from empresas.models import Matriz
from financeiro.models import CentroCusto

class FinanceiroUiCentroCustoBehaviorTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.matriz_a = Matriz.objects.create(nome="Matriz Financeiro R9E A", cnpj="33333333000191")
        cls.matriz_b = Matriz.objects.create(nome="Matriz Financeiro R9E B", cnpj="44444444000191")
        cls.master = Usuario.objects.create_user(username="r9e_master", password="SenhaTeste123!", matriz=cls.matriz_a, perfil=Usuario.PERFIL_MASTER)
        cls.operador = Usuario.objects.create_user(username="r9e_operador_sem_gerenciar", password="SenhaTeste123!", matriz=cls.matriz_a, perfil=Usuario.PERFIL_OPERADOR)
        cls.centro_outra_matriz = CentroCusto.objects.create(matriz=cls.matriz_b, codigo="ZZ-OUTRO", nome="NAO PODE VAZAR", ativo=True)
    def _url(self, name):
        try: return reverse(f"financeiro:{name}")
        except NoReverseMatch as exc: self.fail(f"Rota financeira esperada ausente: financeiro:{name}. Detalhe: {exc}")
    def test_master_com_gerenciar_acessa_listagem_sem_vazar_outra_matriz(self):
        self.client.force_login(self.master); r=self.client.get(self._url("centros_custo")); self.assertEqual(r.status_code,200); self.assertNotContains(r,"NAO PODE VAZAR")
    def test_criacao_vincula_centro_a_matriz_do_usuario(self):
        self.client.force_login(self.master); r=self.client.post(self._url("centro_custo_novo"),{"codigo":"ADM","nome":"Administrativo","ativo":"on","matriz":str(self.matriz_b.pk)}); self.assertIn(r.status_code,(302,303)); c=CentroCusto.objects.get(codigo="ADM",nome="Administrativo"); self.assertEqual(c.matriz_id,self.matriz_a.pk)
    def test_post_nao_pode_forcar_matriz_de_outro_tenant(self):
        self.client.force_login(self.master); self.client.post(self._url("centro_custo_novo"),{"codigo":"COM","nome":"Comercial","ativo":"on","matriz":str(self.matriz_b.pk)}); c=CentroCusto.objects.get(codigo="COM",nome="Comercial"); self.assertEqual(c.matriz_id,self.matriz_a.pk); self.assertNotEqual(c.matriz_id,self.matriz_b.pk)
    def test_usuario_sem_gerenciar_nao_consegue_criar(self):
        self.client.force_login(self.operador); r=self.client.post(self._url("centro_custo_novo"),{"codigo":"BLQ","nome":"Bloqueado","ativo":"on"}); self.assertIn(r.status_code,(302,403,404)); self.assertFalse(CentroCusto.objects.filter(matriz=self.matriz_a,codigo="BLQ",nome="Bloqueado").exists())