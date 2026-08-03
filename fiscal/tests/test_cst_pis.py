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
from fiscal.forms import CSTPISForm
from fiscal.models import CSTPIS
from fiscal.selectors import get_csts_pis
from fiscal.services import criar_cst_pis


class CSTPISModelTests(TestCase):
    def test_seed_cria_trinta_e_tres_codigos(self):
        self.assertEqual(CSTPIS.objects.count(), 33)

    def test_rejeita_codigo_invalido(self):
        with self.assertRaises(ValidationError):
            CSTPIS(
                codigo="1",
                descricao="Invalido",
                tipo_operacao=CSTPIS.TIPO_SAIDA,
            ).full_clean()

    def test_rejeita_descricao_vazia(self):
        with self.assertRaises(ValidationError):
            CSTPIS(
                codigo="10",
                descricao=" ",
                tipo_operacao=CSTPIS.TIPO_SAIDA,
            ).full_clean()


class CSTPISFormTests(TestCase):
    def test_form_valido(self):
        form = CSTPISForm(data={
            "codigo": "10",
            "descricao": " CST PIS de teste ",
            "tipo_operacao": CSTPIS.TIPO_SAIDA,
            "tributado": "on",
            "exige_aliquota": "on",
            "exige_base_calculo": "on",
            "ativo": "on",
        })

        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(
            form.cleaned_data["descricao"],
            "CST PIS de teste",
        )

    def test_codigo_bloqueado_na_edicao(self):
        form = CSTPISForm(
            instance=CSTPIS.objects.get(codigo="01")
        )
        self.assertTrue(form.fields["codigo"].disabled)


class CSTPISSelectorTests(TestCase):
    def test_busca_codigo_exato_e_ativos(self):
        cst = CSTPIS.objects.get(codigo="01")
        cst.ativo = False
        cst.save()

        self.assertFalse(
            get_csts_pis(
                busca="01",
                somente_ativos=True,
            ).exists()
        )

    def test_filtra_tipo_entrada(self):
        resultado = get_csts_pis(
            tipo_operacao=CSTPIS.TIPO_ENTRADA,
        )

        self.assertTrue(resultado.exists())
        self.assertFalse(
            resultado.filter(codigo="01").exists()
        )


class CSTPISServiceTests(TestCase):
    def setUp(self):
        self.matriz = Matriz.objects.create(
            nome="Matriz CST PIS Service",
        )
        User = get_user_model()
        self.usuario = User.objects.create_user(
            username="fiscal_cst_pis_service",
            password="teste123",
            perfil=User.PERFIL_ADMIN_LOJA,
            matriz=self.matriz,
            ativo=True,
        )

    def test_criacao_registra_auditoria(self):
        cst = criar_cst_pis(
            dados={
                "codigo": "10",
                "descricao": "CST PIS de teste",
                "tipo_operacao": CSTPIS.TIPO_SAIDA,
                "tributado": True,
                "exige_aliquota": True,
                "permite_credito": False,
                "exige_base_calculo": True,
                "ativo": True,
            },
            usuario_executor=self.usuario,
            matriz=self.matriz,
        )

        self.assertTrue(
            RegistroAuditoria.objects.filter(
                recurso="fiscal.cst_pis",
                recurso_id=cst.id,
            ).exists()
        )


class CSTPISViewsTests(TestCase):
    def setUp(self):
        self.matriz = Matriz.objects.create(
            nome="Matriz CST PIS",
        )
        User = get_user_model()

        self.admin = User.objects.create_user(
            username="fiscal_admin_cst_pis",
            password="teste123",
            perfil=User.PERFIL_ADMIN_LOJA,
            matriz=self.matriz,
            ativo=True,
        )
        self.operador = User.objects.create_user(
            username="fiscal_operador_cst_pis",
            password="teste123",
            perfil=User.PERFIL_OPERADOR,
            matriz=self.matriz,
            ativo=True,
        )

    def test_lista_exige_login(self):
        self.assertEqual(
            self.client.get(
                reverse("fiscal:lista_csts_pis")
            ).status_code,
            302,
        )

    def test_admin_visualiza_lista(self):
        self.client.force_login(self.admin)
        resposta = self.client.get(
            reverse("fiscal:lista_csts_pis")
        )

        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, "CST PIS")

    def test_operador_sem_permissao_recebe_403(self):
        self.client.force_login(self.operador)

        self.assertEqual(
            self.client.get(
                reverse("fiscal:lista_csts_pis")
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
                reverse("fiscal:lista_csts_pis")
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
                reverse("fiscal:criar_cst_pis")
            ).status_code,
            403,
        )

        PermissaoUsuario.objects.create(
            usuario=self.operador,
            permissao=PERMISSAO_FISCAL_GERENCIAR_CADASTROS,
        )

        self.assertEqual(
            self.client.get(
                reverse("fiscal:criar_cst_pis")
            ).status_code,
            200,
        )
