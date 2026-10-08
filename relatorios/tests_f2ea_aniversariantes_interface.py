from datetime import date
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from empresas.models import Matriz, Loja
from clientes.models import Cliente
from core.choices import StatusOperacional

class RelatorioAniversariantesInterfaceTests(TestCase):
    def setUp(self):
        self.matriz = Matriz.objects.create(nome="Matriz Interface Aniv")
        self.loja = Loja.objects.create(matriz=self.matriz, nome="Loja Interface Aniv", status=StatusOperacional.ATIVA)
        User = get_user_model()
        self.user = User.objects.create_user(username="aniv_interface", password="senha123", perfil=User.PERFIL_OPERADOR, matriz=self.matriz)
        self.user.lojas.add(self.loja)
        self.client.force_login(self.user)
        self.cliente = Cliente.objects.create(matriz=self.matriz, loja_cadastro=self.loja, nome="Ana Aniversariante", tipo_pessoa="PF", data_nascimento=date(1990, 5, 10), telefone="11999999999", email="ana@example.com")

    def test_url_aniversariantes_renderiza_relatorio_e_nao_dashboard(self):
        response = self.client.get(reverse("relatorios:aniversariantes"), {"mes": "5"})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "relatorios/aniversariantes.html")
        self.assertContains(response, "Ana Aniversariante")

    def test_mes_invalido_nao_quebra_e_volta_para_mes_atual(self):
        response = self.client.get(reverse("relatorios:aniversariantes"), {"mes": "99"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("mes_filtro", response.context)
        self.assertGreaterEqual(response.context["mes_filtro"], 1)
        self.assertLessEqual(response.context["mes_filtro"], 12)

    def test_contexto_tem_paginacao_de_50(self):
        response = self.client.get(reverse("relatorios:aniversariantes"), {"mes": "5"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["page_obj"].paginator.per_page, 50)
