from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from empresas.models import Matriz, Loja
from notificacoes.models import AvisoInterno, LeituraAviso


class F27FCrudSinoRedTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        User=get_user_model()
        cls.m=Matriz.objects.create(nome="Matriz CRUD F27F")
        cls.loja=Loja.objects.create(nome="Loja CRUD F27F", matriz=cls.m)
        cls.admin=User.objects.create_user(username="f27fcrudadmin",password="x",matriz=cls.m,perfil="admin_loja")
        cls.op=User.objects.create_user(username="f27fcrudop",password="x",matriz=cls.m,perfil="operador")
        cls.op.lojas.add(cls.loja)
        cls.aviso=AvisoInterno.objects.create(
            matriz=cls.m,titulo="Aviso existente",mensagem="Mensagem",
            criado_por=cls.admin,inicio_exibicao=timezone.now()
        )

    def test_central_lista_avisos_da_matriz(self):
        self.client.force_login(self.admin)
        r=self.client.get(reverse("configuracoes:notificacoes"))
        self.assertEqual(r.status_code,200)
        self.assertContains(r,"Aviso existente")

    def test_admin_consegue_criar_aviso_sem_injetar_matriz(self):
        self.client.force_login(self.admin)
        r=self.client.post(reverse("configuracoes:notificacoes_novo"),{
            "titulo":"Novo comunicado","mensagem":"Equipe, atenção.",
            "prioridade":"atencao","inicio_exibicao":timezone.localtime().strftime("%Y-%m-%dT%H:%M"),
            "fim_exibicao":"","loja":"","ativo":"on",
        })
        self.assertEqual(r.status_code,302)
        a=AvisoInterno.objects.get(titulo="Novo comunicado")
        self.assertEqual(a.matriz_id,self.m.pk)
        self.assertEqual(a.criado_por_id,self.admin.pk)

    def test_operador_nao_acessa_criacao_administrativa(self):
        self.client.force_login(self.op)
        r=self.client.get(reverse("configuracoes:notificacoes_novo"))
        self.assertEqual(r.status_code,403)

    def test_navbar_exibe_sino_e_contagem_nao_lida(self):
        self.client.force_login(self.op)
        r=self.client.get(reverse("notificacoes:lista"))
        self.assertContains(r,'data-notificacoes-sino')
        self.assertContains(r,'data-notificacoes-nao-lidas="1"')

    def test_apos_leitura_contagem_nao_lida_zerada(self):
        LeituraAviso.objects.create(aviso=self.aviso,usuario=self.op)
        self.client.force_login(self.op)
        r=self.client.get(reverse("notificacoes:lista"))
        self.assertContains(r,'data-notificacoes-nao-lidas="0"')

    def test_sino_nao_e_modal_bloqueante(self):
        self.client.force_login(self.op)
        r=self.client.get(reverse("notificacoes:lista"))
        self.assertNotContains(r,'data-notificacoes-modal-bloqueante')
