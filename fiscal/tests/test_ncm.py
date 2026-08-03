from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from accounts.models import PermissaoUsuario
from auditoria.models import RegistroAuditoria
from empresas.models import Matriz
from fiscal.constants import (
    PERMISSAO_FISCAL_GERENCIAR_CADASTROS,
    PERMISSAO_FISCAL_VISUALIZAR,
)
from fiscal.forms import NCMForm
from fiscal.models import NCM
from fiscal.selectors import get_ncms
from fiscal.services import criar_ncm


class NCMModelTests(TestCase):
    def test_seed_cria_seis_ncms(self):
        self.assertEqual(NCM.objects.count(), 6)

    def test_normaliza_codigo_formatado(self):
        ncm = NCM(
            codigo="1234.56.78",
            descricao="NCM formatado de teste",
        )
        ncm.save()
        self.assertEqual(ncm.codigo, "12345678")

    def test_rejeita_codigo_invalido(self):
        with self.assertRaises(ValidationError):
            NCM(
                codigo="2106",
                descricao="Invalido",
            ).full_clean()

    def test_rejeita_descricao_vazia(self):
        with self.assertRaises(ValidationError):
            NCM(
                codigo="99999999",
                descricao=" ",
            ).full_clean()


class NCMFormTests(TestCase):
    def test_form_normaliza_codigo(self):
        form = NCMForm(data={
            "codigo": "8765.43.21",
            "descricao": " NCM de formulario ",
            "unidade_tributavel_padrao": " kg ",
            "ativo": "on",
        })

        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(
            form.cleaned_data["codigo"],
            "87654321",
        )
        self.assertEqual(
            form.cleaned_data["unidade_tributavel_padrao"],
            "KG",
        )

    def test_codigo_bloqueado_na_edicao(self):
        form = NCMForm(
            instance=NCM.objects.get(codigo="21069030")
        )
        self.assertTrue(form.fields["codigo"].disabled)


class NCMSelectorTests(TestCase):
    def test_busca_codigo_formatado_e_ativos(self):
        ncm = NCM.objects.get(codigo="21069030")
        ncm.ativo = False
        ncm.save()

        self.assertFalse(
            get_ncms(
                busca="2106.90.30",
                somente_ativos=True,
            ).exists()
        )

    def test_busca_descricao(self):
        self.assertTrue(
            get_ncms(
                busca="Concentrados de proteinas",
            ).exists()
        )


class NCMServiceTests(TestCase):
    def setUp(self):
        self.matriz = Matriz.objects.create(
            nome="Matriz NCM Service",
        )
        User = get_user_model()
        self.usuario = User.objects.create_user(
            username="fiscal_ncm_service",
            password="teste123",
            perfil=User.PERFIL_ADMIN_LOJA,
            matriz=self.matriz,
            ativo=True,
        )

    def test_criacao_registra_auditoria(self):
        ncm = criar_ncm(
            dados={
                "codigo": "99999999",
                "descricao": "NCM de teste",
                "unidade_tributavel_padrao": "UN",
                "ativo": True,
            },
            usuario_executor=self.usuario,
            matriz=self.matriz,
        )

        self.assertTrue(
            RegistroAuditoria.objects.filter(
                recurso="fiscal.ncm",
                recurso_id=ncm.id,
            ).exists()
        )


class NCMViewsTests(TestCase):
    def setUp(self):
        self.matriz = Matriz.objects.create(
            nome="Matriz NCM",
        )
        User = get_user_model()

        self.admin = User.objects.create_user(
            username="fiscal_admin_ncm",
            password="teste123",
            perfil=User.PERFIL_ADMIN_LOJA,
            matriz=self.matriz,
            ativo=True,
        )
        self.operador = User.objects.create_user(
            username="fiscal_operador_ncm",
            password="teste123",
            perfil=User.PERFIL_OPERADOR,
            matriz=self.matriz,
            ativo=True,
        )

    def test_lista_exige_login(self):
        self.assertEqual(
            self.client.get(
                reverse("fiscal:lista_ncms")
            ).status_code,
            302,
        )

    def test_admin_visualiza_lista(self):
        self.client.force_login(self.admin)
        resposta = self.client.get(
            reverse("fiscal:lista_ncms")
        )

        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, "NCM")

    def test_operador_sem_permissao_recebe_403(self):
        self.client.force_login(self.operador)
        self.assertEqual(
            self.client.get(
                reverse("fiscal:lista_ncms")
            ).status_code,
            403,
        )

    def test_permissao_extra_libera_visualizacao(self):
        PermissaoUsuario.objects.create(
            usuario=self.operador,
            permissao=PERMISSAO_FISCAL_VISUALIZAR,
        )
        self.client.force_login(self.operador)

        self.assertEqual(
            self.client.get(
                reverse("fiscal:lista_ncms")
            ).status_code,
            200,
        )

    def test_criacao_exige_gerenciamento(self):
        PermissaoUsuario.objects.create(
            usuario=self.operador,
            permissao=PERMISSAO_FISCAL_VISUALIZAR,
        )
        self.client.force_login(self.operador)

        self.assertEqual(
            self.client.get(
                reverse("fiscal:criar_ncm")
            ).status_code,
            403,
        )

        PermissaoUsuario.objects.create(
            usuario=self.operador,
            permissao=PERMISSAO_FISCAL_GERENCIAR_CADASTROS,
        )

        self.assertEqual(
            self.client.get(
                reverse("fiscal:criar_ncm")
            ).status_code,
            200,
        )
