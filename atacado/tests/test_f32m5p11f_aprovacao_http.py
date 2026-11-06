from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings
from django.urls import reverse

from atacado.models import (
    ItemOrcamentoAtacado, OrcamentoAtacado, PedidoAtacado,
    StatusOrcamentoAtacado, TransicaoOrcamentoAtacado,
)
from clientes.models import Cliente
from configuracoes.models import ConfiguracaoComercial
from empresas.models import Loja, Matriz
from estoque.models import ReservaEstoque, SaldoEstoque
from produtos.models import Produto, UnidadeMedida


@override_settings(ALLOWED_HOSTS=['testserver', 'localhost', '127.0.0.1'])
class F32M5P11FHTTPTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.matriz = Matriz.objects.create(nome='F32M5P11F Matriz A')
        cls.outra = Matriz.objects.create(nome='F32M5P11F Matriz B')
        cls.loja = Loja.objects.create(matriz=cls.matriz, nome='F32M5P11F Loja A')
        cls.loja2 = Loja.objects.create(matriz=cls.matriz, nome='F32M5P11F Loja A2')
        cls.loja_b = Loja.objects.create(matriz=cls.outra, nome='F32M5P11F Loja B')
        cls.cliente = Cliente.objects.create(matriz=cls.matriz, loja_cadastro=cls.loja, nome='Cliente F32M5P11F')
        cls.cliente_b = Cliente.objects.create(matriz=cls.outra, loja_cadastro=cls.loja_b, nome='Cliente B')
        cls.unidade = UnidadeMedida.objects.create(matriz=cls.matriz, sigla='UN', descricao='Unidade')
        cls.produto = Produto.objects.create(
            matriz=cls.matriz, unidade_medida=cls.unidade,
            codigo_interno='F32M5P11F-001', nome='Produto F32M5P11F',
            preco_venda=Decimal('10.00'),
        )
        ConfiguracaoComercial.objects.create(matriz=cls.matriz, atacado_ativo=True)
        SaldoEstoque.objects.create(matriz=cls.matriz, loja=cls.loja, produto=cls.produto, quantidade_atual=Decimal('10.000'))
        cls.master = get_user_model().objects.create_user(username='f32m5p11f_master', password='F32M5P11F!234')
        cls.master.perfil = 'master'
        cls.master.matriz = cls.matriz
        cls.master.save()

    def orcamento(self, status=StatusOrcamentoAtacado.ENVIADO, quantidade='4.000', loja=None):
        orc = OrcamentoAtacado.objects.create(
            matriz=self.matriz, loja=loja or self.loja, cliente=self.cliente,
            status=status, subtotal_produtos=Decimal('40.00'), total=Decimal('40.00'),
        )
        ItemOrcamentoAtacado.objects.create(
            orcamento=orc, produto=self.produto, quantidade=Decimal(quantidade),
            preco_unitario_original=Decimal('10.00'),
            preco_unitario_base=Decimal('10.00'), preco_unitario_final=Decimal('10.00'),
        )
        return orc

    def post(self, orc, acao, query=''):
        url = reverse('atacado:orcamento_acao', args=[orc.pk]) + query
        return self.client.post(url, {'acao': acao})

    def test_get_rejeitado_405(self):
        self.client.force_login(self.master)
        orc = self.orcamento()
        response = self.client.get(reverse('atacado:orcamento_acao', args=[orc.pk]))
        self.assertEqual(response.status_code, 405)
        self.assertFalse(PedidoAtacado.objects.exists())

    def test_rascunho_enviar_aprovar_e_gerar_uma_vez(self):
        self.client.force_login(self.master)
        orc = self.orcamento(status=StatusOrcamentoAtacado.RASCUNHO)
        self.assertEqual(self.post(orc, 'enviar').status_code, 302)
        orc.refresh_from_db()
        self.assertEqual(orc.status, StatusOrcamentoAtacado.ENVIADO)
        self.assertEqual(self.post(orc, 'aprovar').status_code, 302)
        orc.refresh_from_db()
        self.assertEqual(orc.status, StatusOrcamentoAtacado.PEDIDO_GERADO)
        pedido = PedidoAtacado.objects.get(orcamento_origem=orc)
        self.assertEqual(pedido.total, Decimal('40.00'))
        self.assertEqual(pedido.itens.count(), 1)
        self.assertEqual(ReservaEstoque.objects.count(), 1)
        self.assertEqual(self.post(orc, 'aprovar').status_code, 302)
        self.assertEqual(PedidoAtacado.objects.filter(orcamento_origem=orc).count(), 1)
        self.assertEqual(ReservaEstoque.objects.count(), 1)
        self.assertEqual(TransicaoOrcamentoAtacado.objects.filter(orcamento=orc).count(), 3)

    def test_estoque_insuficiente_desfaz_aprovacao_e_pedido(self):
        self.client.force_login(self.master)
        orc = self.orcamento(quantidade='11.000')
        self.assertEqual(self.post(orc, 'aprovar').status_code, 302)
        orc.refresh_from_db()
        self.assertEqual(orc.status, StatusOrcamentoAtacado.ENVIADO)
        self.assertFalse(PedidoAtacado.objects.filter(orcamento_origem=orc).exists())
        self.assertFalse(ReservaEstoque.objects.exists())
        self.assertFalse(TransicaoOrcamentoAtacado.objects.filter(orcamento=orc).exists())

    def test_falha_injetada_reserva_desfaz_tudo(self):
        self.client.force_login(self.master)
        orc = self.orcamento()
        with patch('atacado.order_services.registrar_reserva_estoque', side_effect=ValidationError('Falha simulada na reserva')):
            self.assertEqual(self.post(orc, 'aprovar').status_code, 302)
        orc.refresh_from_db()
        self.assertEqual(orc.status, StatusOrcamentoAtacado.ENVIADO)
        self.assertFalse(PedidoAtacado.objects.exists())
        self.assertFalse(TransicaoOrcamentoAtacado.objects.exists())

    def test_aprovar_rascunho_nao_altera(self):
        self.client.force_login(self.master)
        orc = self.orcamento(status=StatusOrcamentoAtacado.RASCUNHO)
        self.assertEqual(self.post(orc, 'aprovar').status_code, 302)
        orc.refresh_from_db()
        self.assertEqual(orc.status, StatusOrcamentoAtacado.RASCUNHO)
        self.assertFalse(PedidoAtacado.objects.exists())

    def test_matriz_alheia_retorna_404(self):
        self.client.force_login(self.master)
        orc = OrcamentoAtacado.objects.create(matriz=self.outra, loja=self.loja_b, cliente=self.cliente_b)
        self.assertEqual(self.post(orc, 'enviar').status_code, 404)
        orc.refresh_from_db()
        self.assertEqual(orc.status, StatusOrcamentoAtacado.RASCUNHO)

    def test_loja_nao_autorizada_retorna_404(self):
        usuario = get_user_model().objects.create_user(username='f32m5p11f_admin', password='F32M5P11F!234')
        usuario.perfil = 'admin_loja'
        usuario.matriz = self.matriz
        usuario.save()
        usuario.lojas.add(self.loja)
        self.client.force_login(usuario)
        orc = self.orcamento(loja=self.loja2)
        self.assertEqual(self.post(orc, 'enviar').status_code, 404)

    def test_superuser_exige_matriz_explicita(self):
        superuser = get_user_model().objects.create_superuser(
            username='f32m5p11f_super', email='f32m5p11f@example.test', password='F32M5P11F!234',
        )
        self.client.force_login(superuser)
        orc = self.orcamento(status=StatusOrcamentoAtacado.RASCUNHO)
        self.assertEqual(self.post(orc, 'enviar').status_code, 404)
        self.assertEqual(self.post(orc, 'enviar', '?matriz=999999999').status_code, 404)
        self.assertEqual(self.post(orc, 'enviar', f'?matriz={self.matriz.pk}').status_code, 302)
        orc.refresh_from_db()
        self.assertEqual(orc.status, StatusOrcamentoAtacado.ENVIADO)

    def test_acao_desconhecida_nao_altera(self):
        self.client.force_login(self.master)
        orc = self.orcamento()
        self.assertEqual(self.post(orc, 'acao_invalida').status_code, 404)
        self.assertFalse(PedidoAtacado.objects.exists())

    def test_sem_login_nao_altera(self):
        orc = self.orcamento()
        response = self.post(orc, 'aprovar')
        self.assertEqual(response.status_code, 302)
        self.assertFalse(PedidoAtacado.objects.exists())
