from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from accounts.models import PermissaoUsuario
from empresas.models import Matriz
from fiscal.constants import (
    PERMISSAO_FISCAL_GERENCIAR_CADASTROS,
    PERMISSAO_FISCAL_VISUALIZAR,
)
from fiscal.forms import CFOPForm
from fiscal.models import CFOP
from fiscal.selectors import get_cfops


class CFOPModelTests(TestCase):
    def test_seed_cria_doze_cfops(self):
        self.assertEqual(CFOP.objects.count(), 12)

    def test_classifica_entrada_interna(self):
        self.assertEqual(
            CFOP.classificar_codigo("1102"),
            (CFOP.TIPO_ENTRADA, CFOP.DESTINO_INTERNA),
        )

    def test_classifica_saida_interestadual(self):
        self.assertEqual(
            CFOP.classificar_codigo("6102"),
            (CFOP.TIPO_SAIDA, CFOP.DESTINO_INTERESTADUAL),
        )

    def test_classifica_saida_exterior(self):
        self.assertEqual(
            CFOP.classificar_codigo("7102"),
            (CFOP.TIPO_SAIDA, CFOP.DESTINO_EXTERIOR),
        )

    def test_rejeita_primeiro_digito_invalido(self):
        with self.assertRaises(ValidationError):
            CFOP.classificar_codigo("4102")


class CFOPFormTests(TestCase):
    def test_form_valido(self):
        form = CFOPForm(data={
            "codigo": "5101",
            "descricao": " Venda de producao propria ",
            "gera_movimento_estoque": "on",
            "ativo": "on",
        })
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["descricao"], "Venda de producao propria")

    def test_codigo_bloqueado_na_edicao(self):
        form = CFOPForm(instance=CFOP.objects.get(codigo="5102"))
        self.assertTrue(form.fields["codigo"].disabled)


class CFOPSelectorTests(TestCase):
    def test_busca_codigo_exato_e_ativos(self):
        cfop = CFOP.objects.get(codigo="5102")
        cfop.ativo = False
        cfop.save()
        self.assertFalse(get_cfops(busca="5102", somente_ativos=True).exists())

    def test_filtra_tipo_e_destino(self):
        resultado = get_cfops(
            tipo_operacao=CFOP.TIPO_SAIDA,
            destino_operacao=CFOP.DESTINO_EXTERIOR,
        )
        self.assertEqual(
            list(resultado.values_list("codigo", flat=True)),
            ["7102"],
        )


class CFOPViewsTests(TestCase):
    def setUp(self):
        self.matriz = Matriz.objects.create(nome="Matriz CFOP")
        User = get_user_model()
        self.admin = User.objects.create_user(
            username="fiscal_admin_cfop",
            password="teste123",
            perfil=User.PERFIL_ADMIN_LOJA,
            matriz=self.matriz,
            ativo=True,
        )
        self.operador = User.objects.create_user(
            username="fiscal_operador_cfop",
            password="teste123",
            perfil=User.PERFIL_OPERADOR,
            matriz=self.matriz,
            ativo=True,
        )

    def test_lista_exige_login(self):
        self.assertEqual(
            self.client.get(reverse("fiscal:lista_cfops")).status_code,
            302,
        )

    def test_admin_visualiza_lista(self):
        self.client.force_login(self.admin)
        resposta = self.client.get(reverse("fiscal:lista_cfops"))
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, "CFOP")

    def test_operador_sem_permissao_recebe_403(self):
        self.client.force_login(self.operador)
        self.assertEqual(
            self.client.get(reverse("fiscal:lista_cfops")).status_code,
            403,
        )

    def test_permissao_extra_libera_visualizacao(self):
        PermissaoUsuario.objects.create(
            usuario=self.operador,
            permissao=PERMISSAO_FISCAL_VISUALIZAR,
        )
        self.client.force_login(self.operador)
        self.assertEqual(
            self.client.get(reverse("fiscal:lista_cfops")).status_code,
            200,
        )

    def test_criacao_exige_gerenciamento(self):
        PermissaoUsuario.objects.create(
            usuario=self.operador,
            permissao=PERMISSAO_FISCAL_VISUALIZAR,
        )
        self.client.force_login(self.operador)
        self.assertEqual(
            self.client.get(reverse("fiscal:criar_cfop")).status_code,
            403,
        )

        PermissaoUsuario.objects.create(
            usuario=self.operador,
            permissao=PERMISSAO_FISCAL_GERENCIAR_CADASTROS,
        )
        self.assertEqual(
            self.client.get(reverse("fiscal:criar_cfop")).status_code,
            200,
        )
