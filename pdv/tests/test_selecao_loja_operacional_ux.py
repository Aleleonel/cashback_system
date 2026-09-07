from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import get_resolver, reverse

from empresas.models import Loja, Matriz


class SelecaoVisualLojaOperacionalUxTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.matriz = Matriz.objects.create(nome="Matriz Selecao UX")
        self.loja_a = Loja.objects.create(
            matriz=self.matriz,
            nome="Loja Centro",
        )
        self.loja_b = Loja.objects.create(
            matriz=self.matriz,
            nome="Loja Shopping",
        )
        self.usuario = User.objects.create_user(
            username="operador_multiloja_ux",
            password="teste123",
            perfil=User.PERFIL_OPERADOR,
            matriz=self.matriz,
            ativo=True,
        )
        self.usuario.lojas.add(self.loja_a, self.loja_b)
        self.client.force_login(self.usuario)

    def test_inicio_com_multiplas_lojas_exibe_seletor_operacional(self):
        resposta = self.client.get(reverse("pdv:inicio"))

        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, "Selecione a loja")
        self.assertContains(resposta, self.loja_a.nome)
        self.assertContains(resposta, self.loja_b.nome)

    def test_existe_rota_nomeada_para_selecionar_loja_operacional(self):
        namespace = get_resolver().reverse_dict
        nomes = {key for key in namespace.keys() if isinstance(key, str)}

        # O resolver raiz pode armazenar namespaced routes em resolvers filhos.
        try:
            url = reverse("pdv:selecionar_loja_operacional")
        except Exception:
            url = None

        self.assertIsNotNone(
            url,
            "Deve existir a rota pdv:selecionar_loja_operacional.",
        )

    def test_seletor_visual_envia_loja_por_post(self):
        resposta = self.client.get(reverse("pdv:inicio"))

        self.assertContains(
            resposta,
            'name="loja_operacional_id"',
            html=False,
        )
        self.assertContains(
            resposta,
            'method="post"',
            html=False,
        )

    def test_loja_selecionada_aparece_como_contexto_atual(self):
        session = self.client.session
        session["loja_operacional_id"] = self.loja_b.pk
        session.save()

        resposta = self.client.get(reverse("pdv:inicio"))

        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, "Loja operacional")
        self.assertContains(resposta, self.loja_b.nome)

    def test_usuario_multiloja_pode_ver_acao_trocar_loja(self):
        session = self.client.session
        session["loja_operacional_id"] = self.loja_a.pk
        session.save()

        resposta = self.client.get(reverse("pdv:inicio"))

        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, "Trocar loja")

    def test_sem_loja_selecionada_nao_oferece_abrir_caixa_diretamente(self):
        resposta = self.client.get(reverse("pdv:inicio"))

        self.assertEqual(resposta.status_code, 200)
        self.assertNotContains(
            resposta,
            'data-acao-abrir-caixa="true"',
            html=False,
        )

    def test_admin_nao_recebe_acao_operacional_de_abrir_caixa_por_padrao(self):
        User = get_user_model()
        admin = User.objects.create_user(
            username="admin_matriz_sem_operacao_ux",
            password="teste123",
            perfil=User.PERFIL_ADMIN_LOJA,
            matriz=self.matriz,
            ativo=True,
        )
        admin.lojas.add(self.loja_a, self.loja_b)

        self.client.force_login(admin)
        resposta = self.client.get(reverse("pdv:inicio"))

        self.assertEqual(resposta.status_code, 200)
        self.assertNotContains(
            resposta,
            'data-acao-abrir-caixa="true"',
            html=False,
        )
