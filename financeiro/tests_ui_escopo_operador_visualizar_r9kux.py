from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model

from accounts.models import PermissaoUsuario
from accounts.permissions import PERMISSAO_FINANCEIRO_VISUALIZAR
from empresas.models import Loja
from financeiro.views import _resolver_escopo
from financeiro.selectors import ESCOPO_LOJA


class EscopoOperadorFinanceiroVisualizarR9KUXTests(TestCase):
    def test_operador_com_visualizar_e_loja_autorizada_recebe_escopo_loja(self):
        User = get_user_model()
        matriz_field = User._meta.get_field("matriz")
        Matriz = matriz_field.remote_field.model
        matriz = Matriz.objects.create(nome="Matriz R9KUX15N1")
        loja = Loja.objects.create(matriz=matriz, nome="Loja R9KUX15N1", status="ativa")
        usuario = User.objects.create_user(
            username="operador_r9kux15n1",
            password="teste",
            perfil="operador",
            ativo=True,
            matriz=matriz,
        )
        usuario.lojas.add(loja)
        PermissaoUsuario.objects.create(
            usuario=usuario,
            permissao=PERMISSAO_FINANCEIRO_VISUALIZAR,
        )
        request = RequestFactory().get("/financeiro/titulos/")
        request.user = usuario

        escopo, loja_resolvida, lojas = _resolver_escopo(request, matriz)

        self.assertEqual(escopo, ESCOPO_LOJA)
        self.assertEqual(loja_resolvida.pk, loja.pk)
        self.assertTrue(lojas.filter(pk=loja.pk).exists())