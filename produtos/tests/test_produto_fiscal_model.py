
from decimal import Decimal

from django.db import models
from django.db.models.deletion import ProtectedError
from django.test import TestCase

from empresas.models import Matriz
from fiscal.models import NCM, OrigemMercadoria
from produtos.models import Produto, UnidadeMedida


class ProdutoFiscalModelContractTests(TestCase):
    def setUp(self):
        self.matriz = Matriz.objects.create(nome="Matriz Produto Fiscal")
        self.unidade = UnidadeMedida.objects.create(
            matriz=self.matriz,
            sigla="UN",
            descricao="Unidade",
        )

    def criar_produto(self, **dados):
        valores = {
            "matriz": self.matriz,
            "unidade_medida": self.unidade,
            "codigo_interno": "PROD-FISCAL-001",
            "nome": "Produto Fiscal",
            "custo_base": Decimal("10.00"),
            "preco_venda": Decimal("20.00"),
            "ncm": "21069030",
        }
        valores.update(dados)
        return Produto.objects.create(**valores)

    def test_campos_fiscais_sao_opcionais(self):
        produto = self.criar_produto()
        for campo in (
            "origem_mercadoria",
            "ncm_fiscal",
            "cest",
            "cst_icms",
            "csosn",
            "cst_pis",
            "cst_cofins",
            "cst_ipi",
            "beneficio_fiscal",
            "regra_fiscal_padrao",
        ):
            self.assertIsNone(getattr(produto, campo))
        self.assertFalse(produto.possui_configuracao_fiscal)

    def test_relacionamentos_usam_protect(self):
        for campo in (
            "origem_mercadoria",
            "ncm_fiscal",
            "cest",
            "cst_icms",
            "csosn",
            "cst_pis",
            "cst_cofins",
            "cst_ipi",
            "beneficio_fiscal",
            "regra_fiscal_padrao",
        ):
            field = Produto._meta.get_field(campo)
            self.assertIsInstance(field, models.ForeignKey)
            self.assertIs(field.remote_field.on_delete, models.PROTECT)
            self.assertTrue(field.null)
            self.assertTrue(field.blank)

    def test_ncm_oficial_tem_precedencia_sobre_legado(self):
        ncm = NCM.objects.order_by("codigo").first()
        self.assertIsNotNone(ncm)

        produto = self.criar_produto(
            ncm="21069030",
            ncm_fiscal=ncm,
        )
        self.assertEqual(
            produto.ncm_efetivo,
            ncm.codigo,
        )
        self.assertTrue(produto.possui_configuracao_fiscal)

    def test_ncm_legado_permanece_compativel(self):
        produto = self.criar_produto(ncm="21069030")
        self.assertEqual(produto.ncm_efetivo, "21069030")

    def test_referencia_fiscal_nao_pode_ser_excluida(self):
        origem = (
            OrigemMercadoria.objects
            .order_by("codigo")
            .first()
        )
        self.assertIsNotNone(origem)

        self.criar_produto(
            origem_mercadoria=origem,
        )

        with self.assertRaises(ProtectedError):
            origem.delete()
