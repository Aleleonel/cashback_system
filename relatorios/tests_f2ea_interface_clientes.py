from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from unittest.mock import patch

from empresas.models import Matriz, Loja
from relatorios.views import relatorio_clientes

User = get_user_model()

class RelatorioClientesInterfaceTests(TestCase):
    def setUp(self):
        self.matriz = Matriz.objects.create(nome="Matriz Interface")
        self.loja = Loja.objects.create(matriz=self.matriz, nome="Loja Interface")
        self.user = User.objects.create_user(username="ui_clientes", password="x", perfil=User.PERFIL_OPERADOR, matriz=self.matriz)
        self.user.lojas.add(self.loja)
        self.rf = RequestFactory()

    @patch("relatorios.views.get_relatorio_clientes")
    @patch("relatorios.views.get_contexto_operacional_usuario")
    def test_contexto_expoe_filtros_lojas_e_query_string(self, mock_contexto, mock_selector):
        mock_contexto.return_value = {"matriz": self.matriz, "loja": self.loja}
        mock_selector.return_value = []
        request = self.rf.get("/relatorios/clientes/", {"q":"Maria","ativo":"1","tipo_pessoa":"PF","loja":str(self.loja.pk),"page":"2"})
        request.user = self.user
        with patch("relatorios.views.render") as mock_render:
            relatorio_clientes.__wrapped__.__wrapped__(request)
        ctx = mock_render.call_args.args[2]
        self.assertEqual(ctx["busca"], "Maria")
        self.assertEqual(ctx["ativo_filtro"], "1")
        self.assertEqual(ctx["tipo_pessoa_filtro"], "PF")
        self.assertEqual(ctx["loja_filtro"], str(self.loja.pk))
        self.assertEqual(list(ctx["lojas"]), [self.loja])
        self.assertIn("q=Maria", ctx["query_string"])
        self.assertIn("ativo=1", ctx["query_string"])
        self.assertIn("tipo_pessoa=PF", ctx["query_string"])
        self.assertIn("loja=", ctx["query_string"])

    @patch("relatorios.views.get_contexto_operacional_usuario")
    def test_template_exibe_filtros_campos_contrato_e_paginacao(self, mock_contexto):
        mock_contexto.return_value = {"matriz": self.matriz, "loja": self.loja}
        request = self.rf.get("/relatorios/clientes/")
        request.user = self.user
        response = relatorio_clientes.__wrapped__.__wrapped__(request)
        html = response.content.decode("utf-8")
        dq = chr(34)
        trechos = ["name=" + dq + "q" + dq, "name=" + dq + "ativo" + dq, "name=" + dq + "tipo_pessoa" + dq, "name=" + dq + "loja" + dq, "Cidade/UF", "Cadastro"]
        for trecho in trechos:
            self.assertIn(trecho, html)

    @patch("relatorios.views.get_relatorio_clientes")
    @patch("relatorios.views.get_contexto_operacional_usuario")
    def test_paginacao_preserva_filtros_renderizados(self, mock_contexto, mock_selector):
        mock_contexto.return_value = {"matriz": self.matriz, "loja": self.loja}
        mock_selector.return_value = list(range(51))
        request = self.rf.get("/relatorios/clientes/", {"q":"Maria","ativo":"1","tipo_pessoa":"PF","loja":str(self.loja.pk)})
        request.user = self.user
        response = relatorio_clientes.__wrapped__.__wrapped__(request)
        html = response.content.decode("utf-8")
        self.assertIn("q=Maria", html)
        self.assertIn("ativo=1", html)
        self.assertIn("tipo_pessoa=PF", html)
        self.assertIn("loja=" + str(self.loja.pk), html)
        self.assertIn("page=2", html)
