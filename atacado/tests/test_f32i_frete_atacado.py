from decimal import Decimal
from django.core.exceptions import ValidationError
from django.test import TestCase
from atacado.models import OrcamentoAtacado, PedidoAtacado
from atacado.pricing import ItemPrecificacao, precificar_atacado
from clientes.models import Cliente
from configuracoes.models import ConfiguracaoComercial, FaixaAtacado
from empresas.models import Loja, Matriz
from produtos.models import Produto, UnidadeMedida


class F32IFreteAtacadoTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.matriz=Matriz.objects.create(nome="Matriz F32I")
        cls.loja=Loja.objects.create(matriz=cls.matriz,nome="Loja F32I")
        cls.cliente=Cliente.objects.create(matriz=cls.matriz,loja_cadastro=cls.loja,nome="Cliente F32I")
        cls.un=UnidadeMedida.objects.create(matriz=cls.matriz,sigla="UN",descricao="Unidade")
        cls.produto=Produto.objects.create(matriz=cls.matriz,unidade_medida=cls.un,codigo_interno="I-001",nome="Produto I",custo_base=Decimal("50"),preco_venda=Decimal("100"),atacado_elegivel=True,promocional=False)
        cls.config=ConfiguracaoComercial.objects.create(matriz=cls.matriz,atacado_ativo=True)
        FaixaAtacado.objects.create(configuracao=cls.config,valor_minimo=Decimal("1000"),valor_maximo=None,percentual_desconto=Decimal("10"))

    def test_frete_nao_enquadra_orcamento_na_faixa(self):
        r=precificar_atacado(matriz=self.matriz,itens=[ItemPrecificacao(self.produto,Decimal("9"),Decimal("100"))])
        self.assertEqual(r.base_enquadramento,Decimal("900.00"))
        self.assertIsNone(r.faixa)

    def test_recalculo_total_soma_frete_apos_descontos(self):
        from atacado.models import ItemOrcamentoAtacado
        o=OrcamentoAtacado.objects.create(matriz=self.matriz,loja=self.loja,cliente=self.cliente,frete=Decimal("50"),total=0)
        ItemOrcamentoAtacado.objects.create(orcamento=o,produto=self.produto,quantidade=Decimal("10"),preco_unitario_original=Decimal("100"),preco_unitario_base=Decimal("100"),preco_unitario_final=Decimal("90"),desconto_atacado=Decimal("100"),ajuste_negociado=Decimal("20"))
        o.recalcular_totais()
        self.assertEqual(o.subtotal_produtos,Decimal("1000.00"))
        self.assertEqual(o.desconto_atacado,Decimal("100.00"))
        self.assertEqual(o.ajustes_negociados,Decimal("20.00"))
        self.assertEqual(o.total,Decimal("970.00"))
        self.assertEqual(o.frete,Decimal("50.00"))

    def test_orcamento_rejeita_frete_negativo(self):
        o=OrcamentoAtacado(matriz=self.matriz,loja=self.loja,cliente=self.cliente,frete=Decimal("-0.01"))
        with self.assertRaises(ValidationError):
            o.full_clean()

    def test_pedido_preserva_frete_separado(self):
        f=PedidoAtacado._meta.get_field("frete")
        self.assertEqual(f.decimal_places,2)
        self.assertEqual(f.max_digits,14)
