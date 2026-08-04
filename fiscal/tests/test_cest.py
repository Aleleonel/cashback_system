from datetime import date

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
from fiscal.forms import CESTForm
from fiscal.models import CEST
from fiscal.selectors import get_cests
from fiscal.services import criar_cest


class CESTModelTests(TestCase):
    def test_seed_cria_seis_registros(self):
        self.assertEqual(CEST.objects.count(), 6)

    def test_normaliza_codigo_formatado(self):
        cest = CEST(
            codigo="07.007.00",
            descricao="CEST formatado",
            segmento="Teste",
            ncm_referencia="1234.56.78",
        )
        cest.save()

        self.assertEqual(cest.codigo, "0700700")
        self.assertEqual(
            cest.ncm_referencia,
            "12345678",
        )
        self.assertEqual(
            cest.codigo_formatado,
            "07.007.00",
        )

    def test_rejeita_codigo_invalido(self):
        with self.assertRaises(ValidationError):
            CEST(
                codigo="123",
                descricao="Invalido",
            ).full_clean()

    def test_rejeita_vigencia_invertida(self):
        with self.assertRaises(ValidationError):
            CEST(
                codigo="0700701",
                descricao="Vigencia invalida",
                vigencia_inicio=date(2026, 8, 2),
                vigencia_fim=date(2026, 8, 1),
            ).full_clean()


class CESTFormTests(TestCase):
    def test_form_normaliza_codigos(self):
        form = CESTForm(
            data={
                "codigo": "07.007.02",
                "descricao": " CEST de formulario ",
                "segmento": "Teste",
                "ncm_referencia": "8765.43.21",
                "excecao": "",
                "versao_tabela": "teste",
                "vigencia_inicio": "",
                "vigencia_fim": "",
                "ativo": "on",
            }
        )

        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(
            form.cleaned_data["codigo"],
            "0700702",
        )
        self.assertEqual(
            form.cleaned_data["ncm_referencia"],
            "87654321",
        )

    def test_codigo_bloqueado_na_edicao(self):
        form = CESTForm(
            instance=CEST.objects.first()
        )
        self.assertTrue(
            form.fields["codigo"].disabled
        )


class CESTSelectorTests(TestCase):
    def test_busca_codigo_formatado(self):
        self.assertTrue(
            get_cests(busca="01.001.00").exists()
        )

    def test_busca_por_ncm(self):
        self.assertTrue(
            get_cests(busca="2106.90.30").exists()
        )

    def test_filtra_segmento_e_ativos(self):
        cest = CEST.objects.first()
        cest.ativo = False
        cest.save()

        self.assertFalse(
            get_cests(
                busca=cest.codigo,
                somente_ativos=True,
            ).exists()
        )
        self.assertTrue(
            get_cests(
                segmento="Homologacao",
            ).exists()
        )


class CESTServiceTests(TestCase):
    def setUp(self):
        self.matriz = Matriz.objects.create(
            nome="Matriz CEST Service",
        )
        User = get_user_model()
        self.usuario = User.objects.create_user(
            username="fiscal_cest_service",
            password="teste123",
            perfil=User.PERFIL_ADMIN_LOJA,
            matriz=self.matriz,
            ativo=True,
        )

    def test_criacao_registra_auditoria(self):
        cest = criar_cest(
            dados={
                "codigo": "0700703",
                "descricao": "CEST de teste",
                "segmento": "Teste",
                "ncm_referencia": "12345678",
                "excecao": "",
                "versao_tabela": "teste",
                "vigencia_inicio": None,
                "vigencia_fim": None,
                "ativo": True,
            },
            usuario_executor=self.usuario,
            matriz=self.matriz,
        )

        self.assertTrue(
            RegistroAuditoria.objects.filter(
                recurso="fiscal.cest",
                recurso_id=cest.id,
            ).exists()
        )


class CESTViewsTests(TestCase):
    def setUp(self):
        self.matriz = Matriz.objects.create(
            nome="Matriz CEST",
        )
        User = get_user_model()

        self.admin = User.objects.create_user(
            username="fiscal_admin_cest",
            password="teste123",
            perfil=User.PERFIL_ADMIN_LOJA,
            matriz=self.matriz,
            ativo=True,
        )
        self.operador = User.objects.create_user(
            username="fiscal_operador_cest",
            password="teste123",
            perfil=User.PERFIL_OPERADOR,
            matriz=self.matriz,
            ativo=True,
        )

    def test_lista_exige_login(self):
        self.assertEqual(
            self.client.get(
                reverse("fiscal:lista_cests")
            ).status_code,
            302,
        )

    def test_admin_visualiza_lista(self):
        self.client.force_login(self.admin)
        resposta = self.client.get(
            reverse("fiscal:lista_cests")
        )
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, "CEST")

    def test_operador_sem_permissao_recebe_403(self):
        self.client.force_login(self.operador)
        self.assertEqual(
            self.client.get(
                reverse("fiscal:lista_cests")
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
                reverse("fiscal:lista_cests")
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
                reverse("fiscal:criar_cest")
            ).status_code,
            403,
        )

        PermissaoUsuario.objects.create(
            usuario=self.operador,
            permissao=(
                PERMISSAO_FISCAL_GERENCIAR_CADASTROS
            ),
        )

        self.assertEqual(
            self.client.get(
                reverse("fiscal:criar_cest")
            ).status_code,
            200,
        )
