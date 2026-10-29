from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from auditoria.models import RegistroAuditoria
from auditoria.selectors import get_registros_auditoria
from configuracoes.access import validar_acesso_central_configuracoes
from configuracoes.catalogo import GRUPOS_CONFIGURACAO
from empresas.models import Matriz


class F27CAuditoriaHubContractTests(TestCase):
    def setUp(self):
        self.User = get_user_model()

    def matriz(self, nome, documento):
        campos = {f.name for f in Matriz._meta.fields}
        dados = {}
        if "nome" in campos:
            dados["nome"] = nome
        if "razao_social" in campos:
            dados["razao_social"] = nome
        if "nome_fantasia" in campos:
            dados["nome_fantasia"] = nome
        if "cnpj" in campos:
            dados["cnpj"] = documento
        if "documento" in campos:
            dados["documento"] = documento
        return Matriz.objects.create(**dados)

    def admin(self, username, matriz):
        user = self.User.objects.create_user(username=username, password="f27c")
        if hasattr(user, "ativo"):
            user.ativo = True
        if hasattr(user, "perfil"):
            user.perfil = "master"
        if hasattr(user, "matriz"):
            user.matriz = matriz
        user.save()
        return user

    def test_card_auditoria_disponivel(self):
        grupo = next(g for g in GRUPOS_CONFIGURACAO if g.codigo == "auditoria")
        self.assertTrue(grupo.disponivel)
        self.assertEqual(grupo.url_name, "auditoria:lista_auditoria")

    def test_superuser_mantem_escopo_plataforma(self):
        user = self.User.objects.create_superuser(
            username="su_f27c", email="su@invalid", password="f27c"
        )
        contexto = validar_acesso_central_configuracoes(usuario=user)
        self.assertEqual(contexto["escopo"], "plataforma")
        self.assertIsNone(contexto["matriz"])

    def test_selector_isola_matriz(self):
        matriz_a = self.matriz("F27C A", "11111111000191")
        matriz_b = self.matriz("F27C B", "22222222000191")
        RegistroAuditoria.objects.create(
            matriz=matriz_a, acao=RegistroAuditoria.ACAO_ACESSAR,
            recurso="a", descricao="A_F27C"
        )
        RegistroAuditoria.objects.create(
            matriz=matriz_b, acao=RegistroAuditoria.ACAO_ACESSAR,
            recurso="b", descricao="B_F27C"
        )
        qs = get_registros_auditoria(matriz=matriz_a)
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs.get().matriz_id, matriz_a.pk)

    def test_admin_matriz_acessa_e_fica_isolado(self):
        matriz_a = self.matriz("F27C VISIVEL", "33333333000191")
        matriz_b = self.matriz("F27C OCULTO", "44444444000191")
        user = self.admin("adm_f27c", matriz_a)
        RegistroAuditoria.objects.create(
            matriz=matriz_a, acao=RegistroAuditoria.ACAO_ACESSAR,
            recurso="visivel", descricao="VISIVEL_F27C"
        )
        RegistroAuditoria.objects.create(
            matriz=matriz_b, acao=RegistroAuditoria.ACAO_ACESSAR,
            recurso="oculto", descricao="OCULTO_F27C"
        )
        self.client.force_login(user)
        response = self.client.get(reverse("auditoria:lista_auditoria"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "VISIVEL_F27C")
        self.assertNotContains(response, "OCULTO_F27C")

    def test_operador_nao_acessa(self):
        matriz = self.matriz("F27C OPERADOR", "55555555000191")
        user = self.User.objects.create_user(username="op_f27c", password="f27c")
        if hasattr(user, "ativo"):
            user.ativo = True
        if hasattr(user, "perfil"):
            user.perfil = "operador"
        if hasattr(user, "matriz"):
            user.matriz = matriz
        user.save()
        self.client.force_login(user)
        response = self.client.get(reverse("auditoria:lista_auditoria"))
        self.assertIn(response.status_code, (302, 403))