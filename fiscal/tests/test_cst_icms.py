from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from accounts.models import PermissaoUsuario
from empresas.models import Matriz
from fiscal.constants import PERMISSAO_FISCAL_GERENCIAR_CADASTROS, PERMISSAO_FISCAL_VISUALIZAR
from fiscal.forms import CSTICMSForm
from fiscal.models import CSTICMS
from fiscal.selectors import get_csts_icms

class CSTICMSModelTests(TestCase):
    def test_seed_cria_onze_csts(self):
        self.assertEqual(CSTICMS.objects.count(), 11)
        self.assertEqual(list(CSTICMS.objects.values_list("codigo", flat=True)), ["00", "10", "20", "30", "40", "41", "50", "51", "60", "70", "90"])
    def test_rejeita_codigo_invalido(self):
        with self.assertRaises(ValidationError):
            CSTICMS(codigo="1", descricao="Invalido").full_clean()
    def test_rejeita_descricao_vazia(self):
        with self.assertRaises(ValidationError):
            CSTICMS(codigo="99", descricao=" ").full_clean()

class CSTICMSFormTests(TestCase):
    def test_form_valido(self):
        form = CSTICMSForm(data={"codigo": "99", "descricao": " Outras operacoes ", "exige_aliquota": "on", "ativo": "on"})
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["descricao"], "Outras operacoes")
    def test_codigo_bloqueado_na_edicao(self):
        self.assertTrue(CSTICMSForm(instance=CSTICMS.objects.get(codigo="00")).fields["codigo"].disabled)

class CSTICMSSelectorTests(TestCase):
    def test_busca_codigo_exato_e_ativos(self):
        cst = CSTICMS.objects.get(codigo="00"); cst.ativo = False; cst.save()
        self.assertFalse(get_csts_icms(busca="00", somente_ativos=True).exists())
    def test_busca_textual(self):
        self.assertTrue(get_csts_icms(busca="Tributada integralmente").exists())

class CSTICMSViewsTests(TestCase):
    def setUp(self):
        self.matriz = Matriz.objects.create(nome="Matriz CST ICMS")
        User = get_user_model()
        self.admin = User.objects.create_user(username="fiscal_admin_cst", password="teste123", perfil=User.PERFIL_ADMIN_LOJA, matriz=self.matriz, ativo=True)
        self.operador = User.objects.create_user(username="fiscal_operador_cst", password="teste123", perfil=User.PERFIL_OPERADOR, matriz=self.matriz, ativo=True)
    def test_lista_exige_login(self):
        self.assertEqual(self.client.get(reverse("fiscal:lista_csts_icms")).status_code, 302)
    def test_admin_visualiza_lista(self):
        self.client.force_login(self.admin)
        resposta = self.client.get(reverse("fiscal:lista_csts_icms"))
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, "CST ICMS")
    def test_operador_sem_permissao_recebe_403(self):
        self.client.force_login(self.operador)
        self.assertEqual(self.client.get(reverse("fiscal:lista_csts_icms")).status_code, 403)
    def test_permissao_extra_libera_visualizacao(self):
        PermissaoUsuario.objects.create(usuario=self.operador, permissao=PERMISSAO_FISCAL_VISUALIZAR)
        self.client.force_login(self.operador)
        self.assertEqual(self.client.get(reverse("fiscal:lista_csts_icms")).status_code, 200)
    def test_criacao_exige_gerenciamento(self):
        PermissaoUsuario.objects.create(usuario=self.operador, permissao=PERMISSAO_FISCAL_VISUALIZAR)
        self.client.force_login(self.operador)
        self.assertEqual(self.client.get(reverse("fiscal:criar_cst_icms")).status_code, 403)
        PermissaoUsuario.objects.create(usuario=self.operador, permissao=PERMISSAO_FISCAL_GERENCIAR_CADASTROS)
        self.assertEqual(self.client.get(reverse("fiscal:criar_cst_icms")).status_code, 200)
