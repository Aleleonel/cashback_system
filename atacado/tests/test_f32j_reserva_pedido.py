from decimal import Decimal
from django.core.exceptions import ValidationError
from django.test import TestCase
from atacado.models import OrcamentoAtacado, ItemOrcamentoAtacado, PedidoAtacado, StatusOrcamentoAtacado
from atacado.order_services import gerar_pedido_de_orcamento_aprovado
from clientes.models import Cliente
from configuracoes.models import ConfiguracaoComercial
from empresas.models import Loja, Matriz
from estoque.models import ReservaEstoque, SaldoEstoque
from estoque.choices import StatusReservaEstoque, OrigemMovimentacao
from estoque.selectors import get_saldo_disponivel
from produtos.models import Produto, UnidadeMedida

class F32JReservaPedidoTests(TestCase):
    def setUp(self):
        self.matriz=Matriz.objects.create(nome="Matriz F32J")
        self.loja=Loja.objects.create(matriz=self.matriz,nome="Loja F32J")
        self.cliente=Cliente.objects.create(matriz=self.matriz,loja_cadastro=self.loja,nome="Cliente F32J")
        self.un=UnidadeMedida.objects.create(matriz=self.matriz,sigla="UN",descricao="Unidade")
        self.prod=Produto.objects.create(matriz=self.matriz,unidade_medida=self.un,codigo_interno="J-001",nome="Produto J",preco_venda=Decimal("10"))
        ConfiguracaoComercial.objects.create(matriz=self.matriz,atacado_ativo=True)
        self.saldo=SaldoEstoque.objects.create(matriz=self.matriz,loja=self.loja,produto=self.prod,quantidade_atual=Decimal("10.000"))
    def orcamento(self,q="4.000"):
        o=OrcamentoAtacado.objects.create(matriz=self.matriz,loja=self.loja,cliente=self.cliente,status=StatusOrcamentoAtacado.APROVADO)
        ItemOrcamentoAtacado.objects.create(orcamento=o,produto=self.prod,quantidade=Decimal(q),preco_unitario_original=Decimal("10"),preco_unitario_base=Decimal("10"),preco_unitario_final=Decimal("10"))
        return o
    def test_pedido_cria_reserva_ativa_sem_baixa_fisica(self):
        p=gerar_pedido_de_orcamento_aprovado(self.orcamento())
        r=ReservaEstoque.objects.get()
        self.assertEqual(r.status,StatusReservaEstoque.ATIVA)
        self.assertEqual(r.origem,OrigemMovimentacao.VENDA)
        self.assertEqual(r.quantidade,Decimal("4.000"))
        self.saldo.refresh_from_db()
        self.assertEqual(self.saldo.quantidade_atual,Decimal("10.000"))
        self.assertEqual(get_saldo_disponivel(matriz=self.matriz,loja=self.loja,produto=self.prod),Decimal("6.000"))
        self.assertIn(str(p.pk),r.chave_idempotencia)
    def test_saldo_insuficiente_rollback_pedido_reserva_e_status(self):
        o=self.orcamento("11.000")
        with self.assertRaises(ValidationError):
            gerar_pedido_de_orcamento_aprovado(o)
        o.refresh_from_db()
        self.assertEqual(o.status,StatusOrcamentoAtacado.APROVADO)
        self.assertFalse(PedidoAtacado.objects.filter(orcamento_origem=o).exists())
        self.assertFalse(ReservaEstoque.objects.exists())
    def test_orcamento_aprovado_sem_gerar_pedido_nao_reserva(self):
        self.orcamento()
        self.assertFalse(ReservaEstoque.objects.exists())
    def test_segunda_tentativa_nao_duplica_reserva(self):
        o=self.orcamento()
        gerar_pedido_de_orcamento_aprovado(o)
        self.assertEqual(ReservaEstoque.objects.count(),1)
        with self.assertRaises(ValidationError):
            gerar_pedido_de_orcamento_aprovado(o)
        self.assertEqual(ReservaEstoque.objects.count(),1)
