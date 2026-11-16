"""F32P4H40: regressao HTTP de status efetivo, sem escrita em GET."""
from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from atacado.models import OrcamentoAtacado, StatusOrcamentoAtacado, TransicaoOrcamentoAtacado, PedidoAtacado
from clientes.models import Cliente
from empresas.models import Loja, Matriz


@override_settings(ALLOWED_HOSTS=['testserver', 'localhost', '127.0.0.1'])
class F32P4H40StatusEfetivoHTTPTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.a = Matriz.objects.create(nome='H40 Matriz A')
        cls.b = Matriz.objects.create(nome='H40 Matriz B')
        cls.la = Loja.objects.create(matriz=cls.a, nome='H40 Loja A')
        cls.la2 = Loja.objects.create(matriz=cls.a, nome='H40 Loja A2')
        cls.lb = Loja.objects.create(matriz=cls.b, nome='H40 Loja B')
        cls.ca = Cliente.objects.create(matriz=cls.a, loja_cadastro=cls.la, nome='H40 Cliente A')
        cls.ca2 = Cliente.objects.create(matriz=cls.a, loja_cadastro=cls.la2, nome='H40 Cliente A2')
        cls.cb = Cliente.objects.create(matriz=cls.b, loja_cadastro=cls.lb, nome='H40 Cliente B')
        cls.master = get_user_model().objects.create_user(username='h40_master', password='H40!Test123')
        cls.master.perfil = 'master'
        cls.master.matriz = cls.a
        cls.master.save()

    def make(self, status, validade, *, matriz=None, loja=None, cliente=None):
        return OrcamentoAtacado.objects.create(
            matriz=matriz or self.a, loja=loja or self.la, cliente=cliente or self.ca,
            status=status, valido_ate=validade,
        )

    def url(self):
        return reverse('atacado:orcamentos_lista')

    def login_master(self):
        self.client.force_login(self.master)

    def ids(self, response):
        return {obj.pk for obj in response.context['pagina'].object_list}

    def test_filtros_status_efetivo_sem_escrita(self):
        self.login_master()
        now = timezone.now()
        vencido = self.make(StatusOrcamentoAtacado.ENVIADO, now - timedelta(days=1))
        valido = self.make(StatusOrcamentoAtacado.ENVIADO, now + timedelta(days=1))
        sem_validade = self.make(StatusOrcamentoAtacado.ENVIADO, None)
        expirado = self.make(StatusOrcamentoAtacado.EXPIRADO, now + timedelta(days=1))
        aprovado = self.make(StatusOrcamentoAtacado.APROVADO, now - timedelta(days=1))
        pedido = self.make(StatusOrcamentoAtacado.PEDIDO_GERADO, now - timedelta(days=1))
        antes = list(OrcamentoAtacado.objects.order_by('pk').values_list('pk', 'status', 'atualizado_em', 'expirado_em'))
        for filtro, esperado in (
            ('EXPIRADO', {vencido.pk, expirado.pk}),
            ('ENVIADO', {valido.pk, sem_validade.pk}),
            ('APROVADO', {aprovado.pk}),
            ('PEDIDO_GERADO', {pedido.pk}),
            ('', {vencido.pk, valido.pk, sem_validade.pk, expirado.pk, aprovado.pk, pedido.pk}),
        ):
            with self.subTest(filtro=filtro):
                resposta = self.client.get(self.url(), {'status': filtro})
                self.assertEqual(resposta.status_code, 200)
                self.assertEqual(self.ids(resposta), esperado)
        depois = list(OrcamentoAtacado.objects.order_by('pk').values_list('pk', 'status', 'atualizado_em', 'expirado_em'))
        self.assertEqual(antes, depois)
        self.assertEqual(TransicaoOrcamentoAtacado.objects.count(), 0)

    def test_badge_e_ausencia_acao_aprovar_vencido(self):
        self.login_master()
        vencido = self.make(StatusOrcamentoAtacado.ENVIADO, timezone.now() - timedelta(days=1))
        resposta = self.client.get(self.url(), {'status': 'EXPIRADO'})
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, 'Expirado')
        self.assertIn(vencido.pk, self.ids(resposta))
        self.assertNotContains(resposta, 'data-orcamento="%s"' % vencido.pk)
        self.assertEqual(TransicaoOrcamentoAtacado.objects.count(), 0)

    def test_fronteira_temporal_congelada(self):
        self.login_master()
        instante = timezone.now().replace(microsecond=0)
        igual = self.make(StatusOrcamentoAtacado.ENVIADO, instante)
        with patch('django.utils.timezone.now', return_value=instante):
            self.assertEqual(igual.status_efetivo, StatusOrcamentoAtacado.ENVIADO)
            resposta = self.client.get(self.url(), {'status': 'ENVIADO'})
            self.assertIn(igual.pk, self.ids(resposta))
        with patch('django.utils.timezone.now', return_value=instante + timedelta(microseconds=1)):
            self.assertEqual(igual.status_efetivo, StatusOrcamentoAtacado.EXPIRADO)
            resposta = self.client.get(self.url(), {'status': 'EXPIRADO'})
            self.assertIn(igual.pk, self.ids(resposta))

    def test_isolamento_matriz_e_loja(self):
        now = timezone.now() - timedelta(days=1)
        autorizado = self.make(StatusOrcamentoAtacado.ENVIADO, now)
        outra_loja = self.make(StatusOrcamentoAtacado.ENVIADO, now, loja=self.la2, cliente=self.ca2)
        outra_matriz = self.make(StatusOrcamentoAtacado.ENVIADO, now, matriz=self.b, loja=self.lb, cliente=self.cb)
        self.login_master()
        resposta = self.client.get(self.url(), {'status': 'EXPIRADO'})
        self.assertEqual(self.ids(resposta), {autorizado.pk, outra_loja.pk})
        operador = get_user_model().objects.create_user(username='h40_operador', password='H40!Test123')
        operador.perfil = 'operador'
        operador.matriz = self.a
        operador.save()
        operador.lojas.add(self.la)
        self.client.force_login(operador)
        resposta = self.client.get(self.url(), {'status': 'EXPIRADO'})
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(self.ids(resposta), {autorizado.pk})
        self.assertNotIn(outra_matriz.pk, self.ids(resposta))

    def test_superuser_matriz_explicita(self):
        now = timezone.now() - timedelta(days=1)
        a = self.make(StatusOrcamentoAtacado.ENVIADO, now)
        b = self.make(StatusOrcamentoAtacado.ENVIADO, now, matriz=self.b, loja=self.lb, cliente=self.cb)
        root = get_user_model().objects.create_superuser(username='h40_root', email='h40@example.test', password='H40!Test123')
        self.client.force_login(root)
        self.assertEqual(self.ids(self.client.get(self.url(), {'status': 'EXPIRADO'})), set())
        self.assertEqual(self.ids(self.client.get(self.url(), {'status': 'EXPIRADO', 'matriz': self.a.pk})), {a.pk})
        self.assertEqual(self.ids(self.client.get(self.url(), {'status': 'EXPIRADO', 'matriz': self.b.pk})), {b.pk})

    def test_post_aprovacao_vencido_nao_gera_pedido(self):
        self.login_master()
        vencido = self.make(StatusOrcamentoAtacado.ENVIADO, timezone.now() - timedelta(days=1))
        resposta = self.client.post(reverse('atacado:orcamento_acao', args=[vencido.pk]), {'acao': 'aprovar'})
        self.assertEqual(resposta.status_code, 302)
        vencido.refresh_from_db()
        self.assertEqual(vencido.status, StatusOrcamentoAtacado.ENVIADO)
        self.assertFalse(PedidoAtacado.objects.filter(orcamento_origem=vencido).exists())
        self.assertFalse(TransicaoOrcamentoAtacado.objects.filter(orcamento=vencido).exists())