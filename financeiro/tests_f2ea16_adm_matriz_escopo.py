from django.http import Http404
from django.test import RequestFactory, TestCase
from accounts.models import Usuario
from empresas.models import Loja, Matriz
from financeiro.views import _lojas_relatorio, _resolver_escopo_relatorio
from financeiro.selectors import ESCOPO_CONSOLIDADO, ESCOPO_LOJA

class F2EA16AdmMatrizEscopoTests(TestCase):
    def setUp(self):
        self.rf = RequestFactory()
        self.matriz = Matriz.objects.create(nome="Matriz F2EA16 ADM")
        self.outra_matriz = Matriz.objects.create(nome="Outra Matriz F2EA16")
        self.loja_a = Loja.objects.create(matriz=self.matriz, nome="Loja A")
        self.loja_b = Loja.objects.create(matriz=self.matriz, nome="Loja B")
        self.loja_outra = Loja.objects.create(matriz=self.outra_matriz, nome="Loja Outra")
        self.admin = Usuario.objects.create_user(username="adm_f2ea16", password="x", perfil=Usuario.PERFIL_ADMIN_LOJA, matriz=self.matriz, ativo=True)
        self.admin.lojas.add(self.loja_a)

    def _request(self, query=""):
        request = self.rf.get("/relatorios/financeiro/painel/?" + query)
        request.user = self.admin
        request.session = {}
        return request

    def test_admin_matriz_relatorio_enxerga_todas_lojas_da_propria_matriz(self):
        ids=set(_lojas_relatorio(self._request(),self.matriz).values_list("pk",flat=True))
        self.assertEqual(ids,{self.loja_a.pk,self.loja_b.pk})

    def test_admin_matriz_relatorio_default_consolidado(self):
        escopo,loja,lojas=_resolver_escopo_relatorio(self._request(),self.matriz)
        self.assertEqual(escopo,ESCOPO_CONSOLIDADO); self.assertIsNone(loja)
        self.assertSetEqual(set(lojas.values_list("pk",flat=True)),{self.loja_a.pk,self.loja_b.pk})

    def test_admin_matriz_relatorio_pode_filtrar_qualquer_loja_da_matriz(self):
        escopo,loja,lojas=_resolver_escopo_relatorio(self._request("loja={}".format(self.loja_b.pk)),self.matriz)
        self.assertEqual(escopo,ESCOPO_LOJA); self.assertEqual(loja.pk,self.loja_b.pk)
        self.assertSetEqual(set(lojas.values_list("pk",flat=True)),{self.loja_a.pk,self.loja_b.pk})

    def test_admin_matriz_relatorio_nunca_recebe_loja_de_outra_matriz(self):
        with self.assertRaises(Http404):
            _resolver_escopo_relatorio(self._request("loja={}".format(self.loja_outra.pk)),self.matriz)
