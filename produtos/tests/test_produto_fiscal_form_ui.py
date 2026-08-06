
from decimal import Decimal
from pathlib import Path

from django.test import TestCase

from empresas.models import Matriz
from fiscal.models import CSOSN, CSTICMS, OrigemMercadoria
from produtos.forms import ProdutoForm
from produtos.models import Produto, UnidadeMedida


class ProdutoFiscalFormUIContractTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.matriz = Matriz.objects.create(nome="Matriz Form Fiscal")
        cls.unidade = UnidadeMedida.objects.create(
            matriz=cls.matriz,
            sigla="UN",
            descricao="Unidade",
        )

    def test_form_expoe_campos_fiscais(self):
        form = ProdutoForm(matriz=self.matriz)
        for campo in (
            "origem_mercadoria", "ncm_fiscal", "cest", "cst_icms", "csosn",
            "cst_pis", "cst_cofins", "cst_ipi", "beneficio_fiscal",
            "regra_fiscal_padrao",
        ):
            self.assertIn(campo, form.fields)
            self.assertFalse(form.fields[campo].required)

    def test_form_filtra_referencias_inativas(self):
        origem = OrigemMercadoria.objects.filter(ativo=True).first()
        self.assertIsNotNone(origem)
        OrigemMercadoria.objects.filter(pk=origem.pk).update(ativo=False)
        origem.refresh_from_db()

        form = ProdutoForm(matriz=self.matriz)
        self.assertNotIn(origem, form.fields["origem_mercadoria"].queryset)

    def test_edicao_preserva_referencia_inativa(self):
        origem = OrigemMercadoria.objects.first()
        self.assertIsNotNone(origem)
        OrigemMercadoria.objects.filter(pk=origem.pk).update(ativo=False)
        origem.refresh_from_db()

        produto = Produto.objects.create(
            matriz=self.matriz,
            unidade_medida=self.unidade,
            codigo_interno="PROD-FORM-FISCAL",
            nome="Produto Fiscal",
            custo_base=Decimal("10.00"),
            preco_venda=Decimal("20.00"),
            origem_mercadoria=origem,
        )

        form = ProdutoForm(instance=produto, matriz=self.matriz)
        self.assertIn(origem, form.fields["origem_mercadoria"].queryset)

    def test_form_impede_cst_icms_e_csosn_juntos(self):
        cst = CSTICMS.objects.filter(ativo=True).first()
        csosn = CSOSN.objects.filter(ativo=True).first()
        self.assertIsNotNone(cst)
        self.assertIsNotNone(csosn)

        form = ProdutoForm(
            data={
                "unidade_medida": str(self.unidade.pk),
                "codigo_interno": "PROD-TRIB-001",
                "nome": "Produto Tributacao",
                "custo_base": "10.00",
                "preco_venda": "20.00",
                "cst_icms": str(cst.pk),
                "csosn": str(csosn.pk),
                "status": "ativo",
            },
            matriz=self.matriz,
        )

        self.assertFalse(form.is_valid())
        self.assertIn("cst_icms", form.errors)
        self.assertIn("csosn", form.errors)


class ProdutoFiscalTemplateContractTests(TestCase):
    def test_template_possui_painel_fiscal(self):
        root = Path(__file__).resolve().parents[2]
        template = (
            root / "produtos" / "templates" / "produtos" / "produtos" / "form.html"
        ).read_text(encoding="utf-8")

        for trecho in (
            'data-produto-fiscal="true"',
            "produto-fiscal-panel",
            "form.origem_mercadoria",
            "form.ncm_fiscal",
            "form.cest",
            "form.cst_icms",
            "form.csosn",
            "form.cst_pis",
            "form.cst_cofins",
            "form.cst_ipi",
            "form.beneficio_fiscal",
            "form.regra_fiscal_padrao",
            "produtos/css/produto_fiscal.css",
        ):
            self.assertIn(trecho, template)
