from datetime import date
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from clientes.models import Cliente
from empresas.models import Loja, Matriz

class RelatoriosCadastrosContratoTests(TestCase):
    def setUp(self):
        self.matriz = Matriz.objects.create(nome="Matriz F2EA")
        self.outra_matriz = Matriz.objects.create(nome="Outra Matriz F2EA")
        self.loja = Loja.objects.create(matriz=self.matriz, nome="Loja F2EA")
        self.outra_loja = Loja.objects.create(matriz=self.outra_matriz, nome="Outra Loja F2EA")
        User = get_user_model()
        self.user = User.objects.create_user(username="f2ea", password="teste123")
        # O vÃ­nculo/contexto real do usuÃ¡rio jÃ¡ existe no projeto; a implementaÃ§Ã£o deverÃ¡
        # reutilizÃ¡-lo. Estes testes RED focam primeiro no contrato pÃºblico de URLs.
        self.client.force_login(self.user)

    def test_url_relatorio_clientes_existe(self):
        url = reverse("relatorios:clientes")
        self.assertTrue(url.endswith("/"))

    def test_url_relatorio_aniversariantes_existe(self):
        url = reverse("relatorios:aniversariantes")
        self.assertTrue(url.endswith("/"))

    def test_selector_clientes_publico_existe(self):
        from relatorios import selectors
        self.assertTrue(hasattr(selectors, "get_relatorio_clientes"))

    def test_selector_aniversariantes_publico_existe(self):
        from relatorios import selectors
        self.assertTrue(hasattr(selectors, "get_relatorio_aniversariantes"))

    def test_cliente_possui_campos_minimos_do_contrato(self):
        nomes = {f.name for f in Cliente._meta.get_fields()}
        esperados = {
            "matriz","loja_cadastro","nome","cpf","tipo_pessoa","cnpj",
            "razao_social","nome_fantasia","telefone","email","data_nascimento",
            "cidade","uf","ativo","criado_em",
        }
        self.assertTrue(esperados.issubset(nomes))