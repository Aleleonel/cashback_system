from datetime import timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from atacado.models import ItemOrcamentoAtacado, OrcamentoAtacado, StatusOrcamentoAtacado
from atacado.order_services import gerar_pedido_de_orcamento_aprovado
from clientes.models import Cliente
from configuracoes.models import ConfiguracaoComercial
from empresas.models import Loja, Matriz
from estoque.models import SaldoEstoque
from produtos.models import Produto, UnidadeMedida


class F32HPedidoSnapshotTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.matriz = Matriz.objects.create(nome="Matriz F32H")
        cls.loja = Loja.objects.create(matriz=cls.matriz, nome="Loja F32H")
        cls.cliente = Cliente.objects.create(matriz=cls.matriz, loja_cadastro=cls.loja, nome="Cliente F32H")
        cls.unidade = UnidadeMedida.objects.create(matriz=cls.matriz, sigla="UN", descricao="Unidade")
        cls.produto = Produto.objects.create(
            matriz=cls.matriz, unidade_medida=cls.unidade, codigo_interno="H-001",
            nome="Produto H", custo_base=Decimal("50"), preco_venda=Decimal("100"),
            atacado_elegivel=True, promocional=False,
        )
        cls.config = ConfiguracaoComercial.objects.create(
            matriz=cls.matriz, atacado_ativo=True,
            produto_promocional_conta_para_faixa_atacado=True,
        )

        SaldoEstoque.objects.create(matriz=cls.matriz, loja=cls.loja, produto=cls.produto, quantidade_atual=Decimal("1000.000"))

    def criar(self, status=StatusOrcamentoAtacado.APROVADO, com_item=True):
        o = OrcamentoAtacado.objects.create(
            matriz=self.matriz, loja=self.loja, cliente=self.cliente, status=status,
            valido_ate=timezone.now()+timedelta(days=7),
            subtotal_produtos=Decimal("1000.00"), desconto_atacado=Decimal("100.00"),
            ajustes_negociados=Decimal("0.00"), frete=Decimal("50.00"),
            total=Decimal("950.00"), observacoes="Condição congelada F32H",
        )
        if com_item:
            ItemOrcamentoAtacado.objects.create(
                orcamento=o, produto=self.produto, quantidade=Decimal("10"),
                preco_unitario_original=Decimal("100.00"), preco_unitario_base=Decimal("100.00"),
                preco_unitario_final=Decimal("90.00"), percentual_desconto_atacado=Decimal("10.00"),
                desconto_atacado=Decimal("100.00"), ajuste_negociado=Decimal("0.00"),
                produto_promocional=False, atacado_elegivel=True,
                conta_para_enquadramento=True, justificativa_negociacao="",
            )
        return o

    def test_aprovado_gera_pedido_e_transiciona_status(self):
        o=self.criar()
        p=gerar_pedido_de_orcamento_aprovado(o)
        o.refresh_from_db()
        self.assertEqual(o.status, StatusOrcamentoAtacado.PEDIDO_GERADO)
        self.assertEqual(p.orcamento_origem_id, o.id)

    def test_snapshot_preserva_totais_frete_e_observacoes(self):
        p=gerar_pedido_de_orcamento_aprovado(self.criar())
        self.assertEqual(p.subtotal_produtos, Decimal("1000.00"))
        self.assertEqual(p.desconto_atacado, Decimal("100.00"))
        self.assertEqual(p.frete, Decimal("50.00"))
        self.assertEqual(p.total, Decimal("950.00"))
        self.assertEqual(p.observacoes_snapshot, "Condição congelada F32H")

    def test_snapshot_preserva_item_comercial(self):
        p=gerar_pedido_de_orcamento_aprovado(self.criar())
        i=p.itens.get()
        self.assertEqual(i.quantidade, Decimal("10"))
        self.assertEqual(i.preco_unitario_original, Decimal("100.00"))
        self.assertEqual(i.preco_unitario_final, Decimal("90.00"))
        self.assertEqual(i.percentual_desconto, Decimal("10.00"))
        self.assertEqual(i.desconto_atacado, Decimal("100.00"))
        self.assertTrue(i.atacado_elegivel_snapshot)
        self.assertFalse(i.produto_promocional_snapshot)

    def test_politica_promocional_fica_congelada_no_pedido(self):
        p=gerar_pedido_de_orcamento_aprovado(self.criar())
        self.config.produto_promocional_conta_para_faixa_atacado=False
        self.config.save(update_fields=["produto_promocional_conta_para_faixa_atacado"])
        p.refresh_from_db()
        self.assertTrue(p.produto_promocional_conta_para_faixa_snapshot)

    def test_rejeita_orcamento_nao_aprovado(self):
        with self.assertRaises(ValidationError):
            gerar_pedido_de_orcamento_aprovado(self.criar(StatusOrcamentoAtacado.ENVIADO))

    def test_rejeita_pedido_duplicado(self):
        o=self.criar()
        gerar_pedido_de_orcamento_aprovado(o)
        with self.assertRaises(ValidationError):
            gerar_pedido_de_orcamento_aprovado(o)

    def test_rejeita_orcamento_sem_itens(self):
        with self.assertRaises(ValidationError):
            gerar_pedido_de_orcamento_aprovado(self.criar(com_item=False))
