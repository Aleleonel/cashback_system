from decimal import Decimal
from pathlib import Path

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import resolve, reverse

from empresas.models import Matriz

from configuracoes.forms import ConfiguracaoComercialForm
from configuracoes.models import ConfiguracaoComercial
from configuracoes.views import regras_comerciais


class RegrasComerciaisInterfaceTests(TestCase):
    def setUp(self):
        self.url = reverse("configuracoes:regras_comerciais")
        self.user = get_user_model().objects.create_superuser(
            username="admin_cfg_regras",
            email="admin_cfg_regras@example.com",
            password="senha-segura-123",
        )

    def test_rota_resolve_para_view(self):
        self.assertEqual(resolve(self.url).func, regras_comerciais)

    def test_exige_autenticacao(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.url)

    def test_superusuario_visualiza_tela_no_escopo_plataforma(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "configuracoes/regras_comerciais.html")
        self.assertFalse(response.context["pode_editar_regras"])

    def test_template_possui_formulario(self):
        template = (
            Path(__file__).resolve().parents[1]
            / "templates" / "configuracoes" / "regras_comerciais.html"
        )
        conteudo = template.read_text(encoding="utf-8")
        self.assertIn('method="post"', conteudo)
        self.assertIn("form.pedido_minimo_atacado", conteudo)


class RegrasComerciaisFormTests(TestCase):
    def setUp(self):
        self.matriz = Matriz.objects.create(nome="Matriz CFG Form")
        self.configuracao = ConfiguracaoComercial.objects.create(matriz=self.matriz)

    def test_formulario_valido(self):
        form = ConfiguracaoComercialForm(
            data={
                "atacado_ativo": True,
                "pedido_minimo_atacado": "1000.00",
                "desconto_atacado_percentual": "20.00",
                "cashback_ativo": True,
                "voucher_ativo": True,
                "promocoes_ativas": True,
                "brindes_ativos": True,
                "arredondamento_ativo": False,
            },
            instance=self.configuracao,
        )
        self.assertTrue(form.is_valid(), form.errors)
        salvo = form.save()
        self.assertEqual(salvo.pedido_minimo_atacado, Decimal("1000.00"))

    def test_atacado_ativo_exige_valores_positivos(self):
        form = ConfiguracaoComercialForm(
            data={
                "atacado_ativo": True,
                "pedido_minimo_atacado": "0.00",
                "desconto_atacado_percentual": "0.00",
                "cashback_ativo": True,
                "voucher_ativo": True,
                "promocoes_ativas": True,
                "brindes_ativos": True,
                "arredondamento_ativo": False,
            },
            instance=self.configuracao,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("pedido_minimo_atacado", form.errors)
        self.assertIn("desconto_atacado_percentual", form.errors)

    def test_campos_bloqueados_sem_edicao(self):
        form = ConfiguracaoComercialForm(
            instance=self.configuracao,
            pode_editar=False,
        )
        self.assertTrue(all(campo.disabled for campo in form.fields.values()))
