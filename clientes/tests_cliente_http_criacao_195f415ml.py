import inspect
from unittest.mock import patch

from django.http import HttpResponse
from django.test import RequestFactory, TestCase

from clientes.forms import ClienteForm
from clientes import views
from empresas.models import Matriz, Loja


class CriacaoClienteHttp195F415ML(TestCase):
    def setUp(self):
        self.matriz = Matriz.objects.create(nome="Matriz HTTP ML")
        self.loja = Loja.objects.create(matriz=self.matriz, nome="Loja HTTP ML")

    def test_contexto_deve_existir_no_instance_antes_do_is_valid(self):
        observado = {}

        def is_valid_inspecionado(form):
            observado["matriz_id"] = form.instance.matriz_id
            observado["loja_id"] = form.instance.loja_cadastro_id
            return False

        request = RequestFactory().post("/clientes/novo/", data={
            "tipo_pessoa": "PF",
            "nome": "Cliente Teste HTTP",
            "cpf": "529.982.247-25",
        })
        request.user = object()

        contexto = {"matriz": self.matriz, "loja": self.loja}
        view_original = inspect.unwrap(views.criar_cliente)

        with patch.object(
            views,
            "get_contexto_operacional_usuario",
            return_value=contexto,
        ), patch.object(
            ClienteForm,
            "is_valid",
            is_valid_inspecionado,
        ), patch.object(
            views,
            "render",
            return_value=HttpResponse("FORM_INVALIDO_CONTROLADO", status=200),
        ):
            response = view_original(request)

        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            observado.get("matriz_id"),
            self.matriz.id,
            "A matriz operacional deve estar no form.instance antes de form.is_valid().",
        )
        self.assertEqual(
            observado.get("loja_id"),
            self.loja.id,
            "A loja de cadastro deve estar no form.instance antes de form.is_valid().",
        )
