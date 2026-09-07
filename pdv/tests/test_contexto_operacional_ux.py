from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import Mock

from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase

from accounts.models import Usuario
from empresas.models import Loja, Matriz
from pdv.choices import StatusSessaoCaixa
from pdv.models import Caixa, SessaoCaixa
from pdv import views


class ContextoOperacionalUxContratoTests(TestCase):
    def setUp(self):
        self.rf = RequestFactory()
        self.matriz = Matriz.objects.create(nome="Matriz UX")
        self.loja_a = Loja.objects.create(
            matriz=self.matriz,
            nome="Loja A",
        )
        self.loja_b = Loja.objects.create(
            matriz=self.matriz,
            nome="Loja B",
        )
        self.usuario = get_user_model().objects.create_user(
            username="operador_ux",
            password="x",
            perfil=Usuario.PERFIL_OPERADOR,
            matriz=self.matriz,
        )
        self.usuario.lojas.add(self.loja_a, self.loja_b)

    def _request(self):
        request = self.rf.get("/pdv/")
        request.user = self.usuario
        request.session = {}
        return request

    def test_multiplas_lojas_nao_escolhe_primeira_alfabetica_sem_contexto(self):
        request = self._request()

        matriz, loja, sessao = views._contexto_operacional(request)

        self.assertEqual(matriz, self.matriz)
        self.assertIsNone(
            loja,
            "Com multiplas lojas e sem selecao explicita, o PDV nao deve "
            "escolher silenciosamente a primeira loja alfabetica.",
        )
        self.assertIsNone(sessao)

    def test_loja_operacional_explicita_em_session_e_respeitada(self):
        request = self._request()
        request.session["loja_operacional_id"] = self.loja_b.pk

        matriz, loja, sessao = views._contexto_operacional(request)

        self.assertEqual(matriz, self.matriz)
        self.assertEqual(loja, self.loja_b)
        self.assertIsNone(sessao)

    def test_loja_operacional_nao_autorizada_e_rejeitada(self):
        outra_matriz = Matriz.objects.create(nome="Outra Matriz")
        loja_estranha = Loja.objects.create(
            matriz=outra_matriz,
            nome="Loja Estranha",
        )
        request = self._request()
        request.session["loja_operacional_id"] = loja_estranha.pk

        matriz, loja, sessao = views._contexto_operacional(request)

        self.assertEqual(matriz, self.matriz)
        self.assertIsNone(loja)
        self.assertIsNone(sessao)

    def test_sessao_aberta_do_operador_fixa_contexto_na_loja_do_caixa(self):
        caixa_b = Caixa.objects.create(
            matriz=self.matriz,
            loja=self.loja_b,
            nome="Caixa B",
            codigo="CXB",
        )
        sessao_aberta = SessaoCaixa.objects.create(
            caixa=caixa_b,
            operador_abertura=self.usuario,
            valor_abertura=Decimal("0.00"),
            status=StatusSessaoCaixa.ABERTA,
        )
        request = self._request()
        request.session["loja_operacional_id"] = self.loja_a.pk

        matriz, loja, sessao = views._contexto_operacional(request)

        self.assertEqual(matriz, self.matriz)
        self.assertEqual(
            loja,
            self.loja_b,
            "Sessao aberta deve prevalecer e fixar a loja operacional.",
        )
        self.assertEqual(sessao, sessao_aberta)
        self.assertEqual(
            request.session.get("loja_operacional_id"),
            self.loja_b.pk,
        )

    def test_usuario_com_uma_unica_loja_resolve_contexto_sem_ambiguidade(self):
        self.usuario.lojas.remove(self.loja_b)
        request = self._request()

        matriz, loja, sessao = views._contexto_operacional(request)

        self.assertEqual(matriz, self.matriz)
        self.assertEqual(loja, self.loja_a)
        self.assertIsNone(sessao)
        self.assertEqual(
            request.session.get("loja_operacional_id"),
            self.loja_a.pk,
        )
