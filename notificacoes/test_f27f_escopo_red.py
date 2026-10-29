from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone

from empresas.models import Matriz, Loja
from notificacoes.models import AvisoInterno


class F27FEscopoRedTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.m1 = Matriz.objects.create(nome="Matriz F27F A")
        cls.m2 = Matriz.objects.create(nome="Matriz F27F B")
        cls.l1 = Loja.objects.create(nome="Loja F27F A1", matriz=cls.m1)
        cls.l2 = Loja.objects.create(nome="Loja F27F A2", matriz=cls.m1)
        cls.l3 = Loja.objects.create(nome="Loja F27F B1", matriz=cls.m2)

        cls.admin = User.objects.create_user(
            username="f27f_admin", password="x", matriz=cls.m1, perfil="admin_loja"
        )
        cls.op1 = User.objects.create_user(
            username="f27f_op1", password="x", matriz=cls.m1, perfil="operador"
        )
        cls.op2 = User.objects.create_user(
            username="f27f_op2", password="x", matriz=cls.m1, perfil="operador"
        )
        cls.op3 = User.objects.create_user(
            username="f27f_op3", password="x", matriz=cls.m2, perfil="operador"
        )
        cls.op1.lojas.add(cls.l1)
        cls.op2.lojas.add(cls.l2)
        cls.op3.lojas.add(cls.l3)

        cls.geral = AvisoInterno.objects.create(
            matriz=cls.m1, titulo="Geral M1", mensagem="Todos M1",
            criado_por=cls.admin, inicio_exibicao=timezone.now()
        )
        cls.so_l1 = AvisoInterno.objects.create(
            matriz=cls.m1, loja=cls.l1, titulo="Somente L1", mensagem="L1",
            criado_por=cls.admin, inicio_exibicao=timezone.now()
        )
        cls.futuro = AvisoInterno.objects.create(
            matriz=cls.m1, titulo="Futuro", mensagem="Ainda nao",
            criado_por=cls.admin, inicio_exibicao=timezone.now()+timezone.timedelta(days=1)
        )
        cls.outra = AvisoInterno.objects.create(
            matriz=cls.m2, loja=cls.l3, titulo="Outra matriz", mensagem="M2",
            criado_por=cls.op3, inicio_exibicao=timezone.now()
        )

    def test_operador_lista_apenas_matriz_e_loja_autorizada(self):
        self.client.force_login(self.op1)
        r=self.client.get("/notificacoes/")
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Geral M1")
        self.assertContains(r, "Somente L1")
        self.assertNotContains(r, "Futuro")
        self.assertNotContains(r, "Outra matriz")

    def test_operador_outra_loja_nao_ve_aviso_direcionado(self):
        self.client.force_login(self.op2)
        r=self.client.get("/notificacoes/")
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Geral M1")
        self.assertNotContains(r, "Somente L1")

    def test_operador_nao_pode_marcar_aviso_de_outra_matriz(self):
        self.client.force_login(self.op1)
        r=self.client.post(f"/notificacoes/{self.outra.pk}/marcar-lida/")
        self.assertEqual(r.status_code, 404)

    def test_operador_nao_pode_marcar_aviso_de_outra_loja(self):
        self.client.force_login(self.op2)
        r=self.client.post(f"/notificacoes/{self.so_l1.pk}/marcar-lida/")
        self.assertEqual(r.status_code, 404)

    def test_admin_matriz_acessa_central(self):
        self.client.force_login(self.admin)
        r=self.client.get("/configuracoes/notificacoes/")
        self.assertEqual(r.status_code, 200)

    def test_operador_nao_acessa_central_administrativa(self):
        self.client.force_login(self.op1)
        r=self.client.get("/configuracoes/notificacoes/")
        self.assertEqual(r.status_code, 403)
