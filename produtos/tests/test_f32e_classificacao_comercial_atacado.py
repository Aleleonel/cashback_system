from decimal import Decimal

from django.test import TestCase

from empresas.models import Matriz
from produtos.forms import ProdutoForm
from produtos.models import Categoria, Marca, Produto, UnidadeMedida
from produtos.services import criar_produto, editar_produto


class F32EClassificacaoComercialProdutoTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.matriz = Matriz.objects.create(nome="Matriz F32E")
        cls.categoria = Categoria.objects.create(matriz=cls.matriz, nome="Categoria F32E")
        cls.marca = Marca.objects.create(matriz=cls.matriz, nome="Marca F32E")
        cls.unidade = UnidadeMedida.objects.create(matriz=cls.matriz, sigla="UN", descricao="Unidade")

    def dados(self, **extra):
        base = {
            "categoria": self.categoria,
            "marca": self.marca,
            "unidade_medida": self.unidade,
            "codigo_interno": "F32E-001",
            "sku": "",
            "gtin": "",
            "ncm": "",
            "nome": "Produto F32E",
            "descricao": "",
            "custo_base": Decimal("10.00"),
            "preco_venda": Decimal("20.00"),
            "controla_estoque": True,
            "estoque_minimo": Decimal("0.000"),
            "status": "ativo",
        }
        base.update(extra)
        return base

    def test_modelo_defaults_regular_e_elegivel(self):
        produto = Produto.objects.create(matriz=self.matriz, **self.dados())
        self.assertTrue(produto.atacado_elegivel)
        self.assertFalse(produto.promocional)

    def test_form_expoe_classificacao_comercial(self):
        form = ProdutoForm(matriz=self.matriz)
        self.assertIn("atacado_elegivel", form.fields)
        self.assertIn("promocional", form.fields)

    def test_servico_criacao_persiste_promocional_e_nao_elegivel(self):
        produto = criar_produto(
            matriz=self.matriz,
            dados=self.dados(
                codigo_interno="F32E-002",
                atacado_elegivel=False,
                promocional=True,
            ),
            usuario_executor=None,
        )
        self.assertFalse(produto.atacado_elegivel)
        self.assertTrue(produto.promocional)

    def test_servico_edicao_altera_classificacao_comercial(self):
        produto = Produto.objects.create(
            matriz=self.matriz,
            **self.dados(codigo_interno="F32E-003"),
        )
        dados = self.dados(
            codigo_interno="F32E-003",
            atacado_elegivel=False,
            promocional=True,
        )
        produto = editar_produto(
            produto=produto,
            dados=dados,
            usuario_executor=None,
        )
        produto.refresh_from_db()
        self.assertFalse(produto.atacado_elegivel)
        self.assertTrue(produto.promocional)

    def test_promocional_e_elegibilidade_sao_dimensoes_independentes(self):
        produto = Produto.objects.create(
            matriz=self.matriz,
            **self.dados(
                codigo_interno="F32E-004",
                atacado_elegivel=True,
                promocional=True,
            ),
        )
        self.assertTrue(produto.atacado_elegivel)
        self.assertTrue(produto.promocional)
