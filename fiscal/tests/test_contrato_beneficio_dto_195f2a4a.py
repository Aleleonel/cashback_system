from decimal import Decimal
from types import SimpleNamespace

from django.test import SimpleTestCase

from fiscal.dto_documento_fiscal import DadosItemDocumentoFiscal
from fiscal.services_preparacao_documento_fiscal import _item_snapshot_para_dto


class ContratoBeneficioDTO195F2A4ATests(SimpleTestCase):
    def _item_fiscal(self):
        produto = SimpleNamespace(
            pk=10,
            codigo_interno="P10",
            sku="SKU10",
            nome="Produto teste",
            descricao="",
            gtin="",
            unidade_medida=SimpleNamespace(sigla="UN"),
        )
        item_venda = SimpleNamespace(produto=produto)

        return SimpleNamespace(
            item_venda_id=1,
            item_venda=item_venda,
            origem_mercadoria_codigo="0",
            ncm_codigo="21069030",
            ncm_descricao="NCM teste",
            cest_codigo="",
            cfop_codigo="5102",
            cfop_descricao="Venda",
            cst_icms_codigo="00",
            csosn_codigo="",
            cst_pis_codigo="01",
            cst_cofins_codigo="01",
            cst_ipi_codigo="",
            regime_tributario="normal",
            uf_origem="SP",
            uf_destino="SP",
            tipo_operacao="saida",
            finalidade_operacao="normal",
            contribuinte_icms=False,
            consumidor_final=True,
            quantidade=Decimal("1.000"),
            valor_unitario=Decimal("100.00"),
            valor_produtos=Decimal("100.00"),
            desconto=Decimal("0.00"),
            acrescimo=Decimal("0.00"),
            frete=Decimal("0.00"),
            seguro=Decimal("0.00"),
            outras_despesas=Decimal("0.00"),
            base_operacao=Decimal("100.00"),
            base_icms=Decimal("100.00"),
            percentual_reducao_base_icms=Decimal("0.0000"),
            aliquota_icms=Decimal("18.0000"),
            valor_icms=Decimal("18.00"),
            base_fcp=Decimal("0.00"),
            aliquota_fcp=None,
            valor_fcp=Decimal("0.00"),
            base_pis=Decimal("100.00"),
            aliquota_pis=Decimal("1.6500"),
            valor_pis=Decimal("1.65"),
            base_cofins=Decimal("100.00"),
            aliquota_cofins=Decimal("7.6000"),
            valor_cofins=Decimal("7.60"),
            base_ipi=Decimal("0.00"),
            aliquota_ipi=None,
            valor_ipi=Decimal("0.00"),
            valor_total_tributos=Decimal("27.25"),
            beneficio_fiscal_codigo="BEN-001",
            beneficio_fiscal_descricao="Beneficio teste",
            beneficio_fiscal_tipo="desoneracao",
            beneficio_exige_motivo_desoneracao=True,
            beneficio_motivo_desoneracao="3",
        )

    def test_dto_expoe_campos_com_defaults_neutros(self):
        campos = DadosItemDocumentoFiscal.__dataclass_fields__
        self.assertIn("beneficio_fiscal_codigo", campos)
        self.assertIn("beneficio_fiscal_descricao", campos)
        self.assertIn("beneficio_fiscal_tipo", campos)
        self.assertIn("beneficio_exige_motivo_desoneracao", campos)
        self.assertIn("beneficio_motivo_desoneracao", campos)

        self.assertEqual(campos["beneficio_fiscal_codigo"].default, "")
        self.assertEqual(campos["beneficio_fiscal_descricao"].default, "")
        self.assertEqual(campos["beneficio_fiscal_tipo"].default, "")
        self.assertFalse(campos["beneficio_exige_motivo_desoneracao"].default)
        self.assertEqual(campos["beneficio_motivo_desoneracao"].default, "")

    def test_preparacao_propaga_beneficio_congelado_sem_recalculo(self):
        dto = _item_snapshot_para_dto(self._item_fiscal())

        self.assertEqual(dto.beneficio_fiscal_codigo, "BEN-001")
        self.assertEqual(dto.beneficio_fiscal_descricao, "Beneficio teste")
        self.assertEqual(dto.beneficio_fiscal_tipo, "desoneracao")
        self.assertTrue(dto.beneficio_exige_motivo_desoneracao)
        self.assertEqual(dto.beneficio_motivo_desoneracao, "3")

    def test_preparacao_preserva_defaults_neutros(self):
        item = self._item_fiscal()
        item.beneficio_fiscal_codigo = ""
        item.beneficio_fiscal_descricao = ""
        item.beneficio_fiscal_tipo = ""
        item.beneficio_exige_motivo_desoneracao = False
        item.beneficio_motivo_desoneracao = ""

        dto = _item_snapshot_para_dto(item)

        self.assertEqual(dto.beneficio_fiscal_codigo, "")
        self.assertEqual(dto.beneficio_fiscal_descricao, "")
        self.assertEqual(dto.beneficio_fiscal_tipo, "")
        self.assertFalse(dto.beneficio_exige_motivo_desoneracao)
        self.assertEqual(dto.beneficio_motivo_desoneracao, "")
