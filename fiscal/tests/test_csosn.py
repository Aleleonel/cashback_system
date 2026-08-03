from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from accounts.models import PermissaoUsuario
from empresas.models import Matriz
from fiscal.constants import PERMISSAO_FISCAL_GERENCIAR_CADASTROS, PERMISSAO_FISCAL_VISUALIZAR
from fiscal.forms import CSOSNForm
from fiscal.models import CSOSN
from fiscal.selectors import get_csosns

class CSOSNModelTests(TestCase):
    def test_seed_cria_dez_csosns(self):
        self.assertEqual(CSOSN.objects.count(), 10)
        self.assertEqual(list(CSOSN.objects.values_list("codigo", flat=True)), ["101", "102", "103", "201", "202", "203", "300", "400", "500", "900"])
    def test_rejeita_codigo_invalido(self):
        with self.assertRaises(ValidationError):
            CSOSN(codigo="10", descricao="Invalido").full_clean()
    def test_rejeita_descricao_vazia(self):
        with self.assertRaises(ValidationError):
            CSOSN(codigo="999", descricao=" ").full_clean()

class CSOSNFormTests(TestCase):
    def test_form_valido(self):
        form = CSOSNForm(data={"codigo": "999", "descricao": " Outros ", "exige_aliquota": "on", "ativo": "on"})
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["descricao"], "Outros")
    def test_codigo_bloqueado_na_edicao(self):
        self.assertTrue(CSOSNForm(instance=CSOSN.objects.get(codigo="101")).fields["codigo"].disabled)

class CSOSNSelectorTests(TestCase):
    def test_busca_codigo_exato_e_ativos(self):
        csosn = CSOSN.objects.get(codigo="101"); csosn.ativo = False; csosn.save()
        self.assertFalse(get_csosns(busca="101", somente_ativos=True).exists())
    def test_busca_textual(self):
        self.assertTrue(get_csosns(busca="permissao de credito").exists())

class CSOSNViewsTests(TestCase):
    def setUp(self):
        self.matriz = Matriz.objects.create(nome="Matriz CSOSN")
        User = get_user_model()
        self.admin = User.objects.create_user(username="fiscal_admin_csosn", password="teste123", perfil=User.PERFIL_ADMIN_LOJA, matriz=self.matriz, ativo=True)
        self.operador = User.objects.create_user(username="fiscal_operador_csosn", password="teste123", perfil=User.PERFIL_OPERADOR, matriz=self.matriz, ativo=True)
    def test_lista_exige_login(self):
        self.assertEqual(self.client.get(reverse("fiscal:lista_csosns")).status_code, 302)
    def test_admin_visualiza_lista(self):
        self.client.force_login(self.admin)
        resposta = self.client.get(reverse("fiscal:lista_csosns"))
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, "CSOSN")
    def test_operador_sem_permissao_recebe_403(self):
        self.client.force_login(self.operador)
        self.assertEqual(self.client.get(reverse("fiscal:lista_csosns")).status_code, 403)
    def test_permissao_extra_libera_visualizacao(self):
        PermissaoUsuario.objects.create(usuario=self.operador, permissao=PERMISSAO_FISCAL_VISUALIZAR)
        self.client.force_login(self.operador)
        self.assertEqual(self.client.get(reverse("fiscal:lista_csosns")).status_code, 200)
    def test_criacao_exige_gerenciamento(self):
        PermissaoUsuario.objects.create(usuario=self.operador, permissao=PERMISSAO_FISCAL_VISUALIZAR)
        self.client.force_login(self.operador)
        self.assertEqual(self.client.get(reverse("fiscal:criar_csosn")).status_code, 403)
        PermissaoUsuario.objects.create(usuario=self.operador, permissao=PERMISSAO_FISCAL_GERENCIAR_CADASTROS)
        self.assertEqual(self.client.get(reverse("fiscal:criar_csosn")).status_code, 200)
