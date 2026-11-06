from decimal import Decimal
from pathlib import Path

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import resolve, reverse

from empresas.models import Matriz
from configuracoes.forms import ConfiguracaoComercialForm
from configuracoes.forms_atacado import PoliticaAtacadoForm
from configuracoes.models import ConfiguracaoComercial
from configuracoes.views import regras_comerciais


class RegrasComerciaisInterfaceTests(TestCase):
    def setUp(self):
        self.url = reverse("configuracoes:regras_comerciais")
        self.user = get_user_model().objects.create_superuser(
            username="admin_cfg_regras", email="admin_cfg_regras@example.com",
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

    def test_template_geral_nao_duplica_politica_atacado(self):
        template = Path(__file__).resolve().parents[1] / "templates" / "configuracoes" / "regras_comerciais.html"
        conteudo = template.read_text(encoding="utf-8")
        self.assertIn('method="post"', conteudo)
        self.assertNotIn("form.pedido_minimo_atacado", conteudo)
        self.assertNotIn("form.desconto_atacado_percentual", conteudo)
        self.assertNotIn("form.atacado_ativo", conteudo)
        self.assertIn("configuracoes:politica_atacado", conteudo)

    def test_template_politica_contem_pedido_minimo(self):
        template = Path(__file__).resolve().parents[1] / "templates" / "configuracoes" / "politica_atacado.html"
        conteudo = template.read_text(encoding="utf-8")
        self.assertIn("form.pedido_minimo_atacado", conteudo)
        self.assertIn("form.atacado_ativo", conteudo)


class RegrasComerciaisFormTests(TestCase):
    def setUp(self):
        self.matriz = Matriz.objects.create(nome="Matriz CFG Form")
        self.configuracao = ConfiguracaoComercial.objects.create(matriz=self.matriz)

    def test_formulario_geral_valido_sem_campos_atacado(self):
        form = ConfiguracaoComercialForm(data={
            "cashback_ativo": True, "voucher_ativo": True,
            "promocoes_ativas": True, "brindes_ativos": True,
            "arredondamento_ativo": False,
        }, instance=self.configuracao)
        self.assertTrue(form.is_valid(), form.errors)
        self.assertNotIn("atacado_ativo", form.fields)
        self.assertNotIn("pedido_minimo_atacado", form.fields)
        self.assertNotIn("desconto_atacado_percentual", form.fields)
        form.save()
        self.configuracao.refresh_from_db()
        self.assertFalse(self.configuracao.atacado_ativo)
        self.assertEqual(self.configuracao.pedido_minimo_atacado, Decimal("0.00"))

    def test_politica_atacado_e_dona_do_pedido_minimo(self):
        form = PoliticaAtacadoForm(data={
            "atacado_ativo": True,
            "pedido_minimo_atacado": "750.00",
            "produto_promocional_conta_para_faixa_atacado": True,
        }, instance=self.configuracao)
        self.assertTrue(form.is_valid(), form.errors)
        form.save()
        self.configuracao.refresh_from_db()
        self.assertTrue(self.configuracao.atacado_ativo)
        self.assertEqual(self.configuracao.pedido_minimo_atacado, Decimal("750.00"))
        self.assertTrue(self.configuracao.produto_promocional_conta_para_faixa_atacado)

    def test_politica_rejeita_pedido_minimo_negativo(self):
        form = PoliticaAtacadoForm(data={
            "atacado_ativo": True,
            "pedido_minimo_atacado": "-1.00",
        }, instance=self.configuracao)
        self.assertFalse(form.is_valid())
        self.assertIn("pedido_minimo_atacado", form.errors)

    def test_campos_gerais_bloqueados_sem_edicao(self):
        form = ConfiguracaoComercialForm(instance=self.configuracao, pode_editar=False)
        self.assertTrue(all(campo.disabled for campo in form.fields.values()))
