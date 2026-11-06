from decimal import Decimal
from django.core.exceptions import ValidationError
from django.test import TestCase
from atacado.models import OrcamentoAtacado, ItemOrcamentoAtacado, StatusOrcamentoAtacado, StatusPedidoAtacado
from atacado.order_services import gerar_pedido_de_orcamento_aprovado, finalizar_pedido_atacado, cancelar_pedido_atacado
from clientes.models import Cliente
from configuracoes.models import ConfiguracaoComercial
from empresas.models import Loja, Matriz
from estoque.models import ReservaEstoque, SaldoEstoque
from estoque.choices import StatusReservaEstoque
from estoque.selectors import get_saldo_disponivel
from produtos.models import Produto, UnidadeMedida

class F32JCicloOperacionalTests(TestCase):
    def setUp(self):
        self.matriz=Matriz.objects.create(nome="Matriz F32J7")
        self.loja=Loja.objects.create(matriz=self.matriz,nome="Loja F32J7")
        self.cliente=Cliente.objects.create(matriz=self.matriz,loja_cadastro=self.loja,nome="Cliente F32J7")
        self.un=UnidadeMedida.objects.create(matriz=self.matriz,sigla="UN",descricao="Unidade")
        self.prod=Produto.objects.create(matriz=self.matriz,unidade_medida=self.un,codigo_interno="J7-001",nome="Produto J7",preco_venda=Decimal("10"))
        ConfiguracaoComercial.objects.create(matriz=self.matriz,atacado_ativo=True)
        self.saldo=SaldoEstoque.objects.create(matriz=self.matriz,loja=self.loja,produto=self.prod,quantidade_atual=Decimal("10.000"))
    def pedido(self):
        o=OrcamentoAtacado.objects.create(matriz=self.matriz,loja=self.loja,cliente=self.cliente,status=StatusOrcamentoAtacado.APROVADO)
        ItemOrcamentoAtacado.objects.create(orcamento=o,produto=self.prod,quantidade=Decimal("4.000"),preco_unitario_original=Decimal("10"),preco_unitario_base=Decimal("10"),preco_unitario_final=Decimal("10"))
        return gerar_pedido_de_orcamento_aprovado(o)
    def test_finalizar_confirma_reserva_e_baixa_fisica(self):
        p=self.pedido();self.assertEqual(get_saldo_disponivel(matriz=self.matriz,loja=self.loja,produto=self.prod),Decimal("6.000"))
        finalizar_pedido_atacado(pedido=p)
        p.refresh_from_db();r=ReservaEstoque.objects.get();self.saldo.refresh_from_db()
        self.assertEqual(p.status,StatusPedidoAtacado.FINALIZADO);self.assertIsNotNone(p.finalizado_em)
        self.assertEqual(r.status,StatusReservaEstoque.CONFIRMADA)
        self.assertEqual(self.saldo.quantidade_atual,Decimal("6.000"))
        self.assertEqual(get_saldo_disponivel(matriz=self.matriz,loja=self.loja,produto=self.prod),Decimal("6.000"))
    def test_cancelar_libera_reserva_sem_baixa_fisica(self):
        p=self.pedido();cancelar_pedido_atacado(pedido=p)
        p.refresh_from_db();r=ReservaEstoque.objects.get();self.saldo.refresh_from_db()
        self.assertEqual(p.status,StatusPedidoAtacado.CANCELADO);self.assertIsNotNone(p.cancelado_em)
        self.assertEqual(r.status,StatusReservaEstoque.LIBERADA)
        self.assertEqual(self.saldo.quantidade_atual,Decimal("10.000"))
        self.assertEqual(get_saldo_disponivel(matriz=self.matriz,loja=self.loja,produto=self.prod),Decimal("10.000"))
    def test_finalizacao_idempotente_nao_duplica_baixa(self):
        p=self.pedido();finalizar_pedido_atacado(pedido=p);finalizar_pedido_atacado(pedido=p)
        self.saldo.refresh_from_db()
        self.assertEqual(self.saldo.quantidade_atual,Decimal("6.000"))
        self.assertEqual(ReservaEstoque.objects.count(),1)
    def test_cancelamento_idempotente(self):
        p=self.pedido();cancelar_pedido_atacado(pedido=p);cancelar_pedido_atacado(pedido=p)
        self.assertEqual(ReservaEstoque.objects.count(),1)
        self.assertEqual(ReservaEstoque.objects.get().status,StatusReservaEstoque.LIBERADA)
    def test_finalizado_nao_pode_cancelar(self):
        p=self.pedido();finalizar_pedido_atacado(pedido=p)
        with self.assertRaises(ValidationError): cancelar_pedido_atacado(pedido=p)
    def test_cancelado_nao_pode_finalizar(self):
        p=self.pedido();cancelar_pedido_atacado(pedido=p)
        with self.assertRaises(ValidationError): finalizar_pedido_atacado(pedido=p)
