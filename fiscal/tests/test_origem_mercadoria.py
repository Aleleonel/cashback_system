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
from fiscal.forms import OrigemMercadoriaForm
from fiscal.models import OrigemMercadoria
from fiscal.selectors import get_origens_mercadoria


class OrigemMercadoriaModelTests(TestCase):
    def test_seed_cria_nove_origens(self):
        self.assertEqual(
            OrigemMercadoria.objects.count(),
            9,
        )
        self.assertEqual(
            list(
                OrigemMercadoria.objects.values_list(
                    "codigo",
                    flat=True,
                )
            ),
            list("012345678"),
        )

    def test_normaliza_campos(self):
        origem = OrigemMercadoria.objects.get(codigo="0")
        origem.descricao = "  Nacional  "
        origem.save()

        self.assertEqual(origem.descricao, "Nacional")

    def test_rejeita_codigo_fora_da_faixa(self):
        origem = OrigemMercadoria(
            codigo="9",
            descricao="Invalida",
        )

        with self.assertRaises(ValidationError):
            origem.full_clean()

    def test_rejeita_descricao_vazia(self):
        origem = OrigemMercadoria(
            codigo="0",
            descricao=" ",
        )

        with self.assertRaises(ValidationError):
            origem.full_clean()


class OrigemMercadoriaFormTests(TestCase):
    def test_form_valido(self):
        OrigemMercadoria.objects.filter(codigo="0").delete()

        form = OrigemMercadoriaForm(
            data={
                "codigo": "0",
                "descricao": " Nacional ",
                "ativo": "on",
            }
        )

        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(
            form.cleaned_data["descricao"],
            "Nacional",
        )

    def test_codigo_fica_bloqueado_na_edicao(self):
        origem = OrigemMercadoria.objects.get(codigo="0")
        form = OrigemMercadoriaForm(instance=origem)

        self.assertTrue(form.fields["codigo"].disabled)


class OrigemMercadoriaSelectorTests(TestCase):
    def test_filtra_codigo_exato_e_ativas(self):
        origem = OrigemMercadoria.objects.get(codigo="0")
        origem.ativo = False
        origem.save()

        resultado = get_origens_mercadoria(
            busca="0",
            somente_ativas=True,
        )

        self.assertFalse(resultado.exists())

    def test_busca_textual_pela_descricao(self):
        self.assertTrue(
            get_origens_mercadoria(
                busca="Nacional",
            ).exists()
        )


class OrigemMercadoriaViewsTests(TestCase):
    def setUp(self):
        self.matriz = Matriz.objects.create(
            nome="Matriz Fiscal",
        )
        User = get_user_model()

        self.admin = User.objects.create_user(
            username="fiscal_admin_origem",
            password="teste123",
            perfil=User.PERFIL_ADMIN_LOJA,
            matriz=self.matriz,
            ativo=True,
        )
        self.operador = User.objects.create_user(
            username="fiscal_operador_origem",
            password="teste123",
            perfil=User.PERFIL_OPERADOR,
            matriz=self.matriz,
            ativo=True,
        )

    def test_lista_exige_login(self):
        resposta = self.client.get(
            reverse("fiscal:lista_origens_mercadoria")
        )

        self.assertEqual(resposta.status_code, 302)

    def test_admin_visualiza_lista(self):
        self.client.force_login(self.admin)

        resposta = self.client.get(
            reverse("fiscal:lista_origens_mercadoria")
        )

        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, "Origens da mercadoria")

    def test_operador_sem_permissao_recebe_403(self):
        self.client.force_login(self.operador)

        resposta = self.client.get(
            reverse("fiscal:lista_origens_mercadoria")
        )

        self.assertEqual(resposta.status_code, 403)

    def test_permissao_extra_libera_visualizacao(self):
        PermissaoUsuario.objects.create(
            usuario=self.operador,
            permissao=PERMISSAO_FISCAL_VISUALIZAR,
        )
        self.client.force_login(self.operador)

        resposta = self.client.get(
            reverse("fiscal:lista_origens_mercadoria")
        )

        self.assertEqual(resposta.status_code, 200)

    def test_criacao_exige_permissao_de_gerenciamento(self):
        PermissaoUsuario.objects.create(
            usuario=self.operador,
            permissao=PERMISSAO_FISCAL_VISUALIZAR,
        )
        self.client.force_login(self.operador)

        resposta = self.client.get(
            reverse("fiscal:criar_origem_mercadoria")
        )

        self.assertEqual(resposta.status_code, 403)

        PermissaoUsuario.objects.create(
            usuario=self.operador,
            permissao=PERMISSAO_FISCAL_GERENCIAR_CADASTROS,
        )

        resposta = self.client.get(
            reverse("fiscal:criar_origem_mercadoria")
        )

        self.assertEqual(resposta.status_code, 200)
