from decimal import Decimal

from django.test import TestCase

from atacado.pricing import ItemPrecificacao, precificar_atacado
from configuracoes.models import ConfiguracaoComercial, FaixaAtacado
from empresas.models import Matriz
from produtos.models import Produto, UnidadeMedida


class F32GMotorPrecificacaoAtacadoTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.matriz = Matriz.objects.create(nome="Matriz F32G")
        cls.unidade = UnidadeMedida.objects.create(matriz=cls.matriz, sigla="UN", descricao="Unidade")
        cls.config = ConfiguracaoComercial.objects.create(
            matriz=cls.matriz,
            atacado_ativo=True,
            produto_promocional_conta_para_faixa_atacado=True,
        )
        cls.faixa_1000 = FaixaAtacado.objects.create(
            configuracao=cls.config,
            valor_minimo=Decimal("1000.00"),
            valor_maximo=Decimal("1999.99"),
            percentual_desconto=Decimal("10.00"),
        )
        cls.faixa_2000 = FaixaAtacado.objects.create(
            configuracao=cls.config,
            valor_minimo=Decimal("2000.00"),
            valor_maximo=None,
            percentual_desconto=Decimal("15.00"),
        )
        cls.regular = Produto.objects.create(
            matriz=cls.matriz, unidade_medida=cls.unidade, codigo_interno="G-REG",
            nome="Regular", custo_base=Decimal("50"), preco_venda=Decimal("100"),
            atacado_elegivel=True, promocional=False,
        )
        cls.promo = Produto.objects.create(
            matriz=cls.matriz, unidade_medida=cls.unidade, codigo_interno="G-PRO",
            nome="Promo", custo_base=Decimal("50"), preco_venda=Decimal("100"),
            atacado_elegivel=True, promocional=True,
        )
        cls.nao_elegivel = Produto.objects.create(
            matriz=cls.matriz, unidade_medida=cls.unidade, codigo_interno="G-NE",
            nome="Nao elegivel", custo_base=Decimal("50"), preco_venda=Decimal("100"),
            atacado_elegivel=False, promocional=False,
        )

    def item(self, produto, qtd, preco="100"):
        return ItemPrecificacao(produto=produto, quantidade=Decimal(str(qtd)), preco_unitario=Decimal(str(preco)))

    def test_enquadra_faixa_progressiva_por_valor(self):
        r=precificar_atacado(matriz=self.matriz,itens=[self.item(self.regular,10)])
        self.assertEqual(r.base_enquadramento,Decimal("1000.00"))
        self.assertEqual(r.percentual_desconto,Decimal("10.00"))
        self.assertEqual(r.desconto_atacado,Decimal("100.00"))

    def test_promocional_conta_para_faixa_mas_nao_recebe_desconto(self):
        r=precificar_atacado(matriz=self.matriz,itens=[self.item(self.regular,8),self.item(self.promo,3)])
        self.assertEqual(r.base_enquadramento,Decimal("1100.00"))
        self.assertEqual(r.desconto_atacado,Decimal("80.00"))
        promo=[x for x in r.itens if x.produto_id == self.promo.id] if False else [x for x in r.itens if x.produto.id == self.promo.id]
        self.assertEqual(promo[0].desconto_atacado,Decimal("0.00"))

    def test_promocional_pode_ser_excluido_do_enquadramento_pela_matriz(self):
        self.config.produto_promocional_conta_para_faixa_atacado=False
        self.config.save(update_fields=["produto_promocional_conta_para_faixa_atacado"])
        r=precificar_atacado(matriz=self.matriz,itens=[self.item(self.regular,8),self.item(self.promo,3)])
        self.assertEqual(r.base_enquadramento,Decimal("800.00"))
        self.assertIsNone(r.faixa)
        self.assertEqual(r.desconto_atacado,Decimal("0.00"))

    def test_nao_elegivel_conta_para_faixa_mas_nao_recebe_desconto(self):
        r=precificar_atacado(matriz=self.matriz,itens=[self.item(self.regular,8),self.item(self.nao_elegivel,3)])
        self.assertEqual(r.base_enquadramento,Decimal("1100.00"))
        self.assertEqual(r.desconto_atacado,Decimal("80.00"))

    def test_frete_nao_participa_do_motor_de_enquadramento(self):
        r=precificar_atacado(matriz=self.matriz,itens=[self.item(self.regular,9)])
        self.assertEqual(r.base_enquadramento,Decimal("900.00"))
        self.assertIsNone(r.faixa)

    def test_segunda_faixa_aplica_percentual_maior(self):
        r=precificar_atacado(matriz=self.matriz,itens=[self.item(self.regular,20)])
        self.assertEqual(r.percentual_desconto,Decimal("15.00"))
        self.assertEqual(r.desconto_atacado,Decimal("300.00"))

    def test_totais_sao_deterministicos_em_centavos(self):
        r=precificar_atacado(matriz=self.matriz,itens=[self.item(self.regular,10,"33.33")])
        self.assertEqual(r.subtotal_produtos,Decimal("333.30"))
        self.assertEqual(r.total_produtos,Decimal("333.30"))
