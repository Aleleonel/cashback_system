from dataclasses import FrozenInstanceError
from decimal import Decimal

from django.test import SimpleTestCase

from fiscal.dto_documento_fiscal import (
    DadosDocumentoFiscal,
    DadosItemDocumentoFiscal,
)


class DadosDocumentoFiscalTests(SimpleTestCase):
    def item(self):
        return DadosItemDocumentoFiscal(
            item_venda_id=1,
            origem_mercadoria_codigo="0",
            ncm_codigo="21069090",
            ncm_descricao="Teste",
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
            finalidade_operacao="venda",
            contribuinte_icms=False,
            consumidor_final=True,
            quantidade=Decimal("1.000"),
            valor_unitario=Decimal("10.00"),
            valor_produtos=Decimal("10.00"),
            desconto=Decimal("0.00"),
            acrescimo=Decimal("0.00"),
            frete=Decimal("0.00"),
            seguro=Decimal("0.00"),
            outras_despesas=Decimal("0.00"),
            base_operacao=Decimal("10.00"),
            base_icms=Decimal("10.00"),
            aliquota_icms=Decimal("18.0000"),
            valor_icms=Decimal("1.80"),
            base_fcp=Decimal("0.00"),
            aliquota_fcp=None,
            valor_fcp=Decimal("0.00"),
            base_pis=Decimal("10.00"),
            aliquota_pis=Decimal("1.6500"),
            valor_pis=Decimal("0.17"),
            base_cofins=Decimal("10.00"),
            aliquota_cofins=Decimal("7.6000"),
            valor_cofins=Decimal("0.76"),
            base_ipi=Decimal("0.00"),
            aliquota_ipi=None,
            valor_ipi=Decimal("0.00"),
            valor_total_tributos=Decimal("2.73"),
        )

    def test_dto_item_e_imutavel(self):
        item = self.item()

        with self.assertRaises(FrozenInstanceError):
            item.ncm_codigo = "99999999"

    def test_dto_documento_aceita_tuple_de_itens(self):
        item = self.item()

        dados = DadosDocumentoFiscal(
            venda_fiscal_id=1,
            venda_id=1,
            matriz_id=1,
            loja_id=1,
            modelo="65",
            ambiente="homologacao",
            serie=1,
            numero=None,
            regime_tributario="normal",
            uf_origem="SP",
            uf_destino="SP",
            tipo_operacao="saida",
            finalidade_operacao="venda",
            contribuinte_icms=False,
            consumidor_final=True,
            total_base_operacao=Decimal("10.00"),
            total_base_icms=Decimal("10.00"),
            total_icms=Decimal("1.80"),
            total_fcp=Decimal("0.00"),
            total_base_pis=Decimal("10.00"),
            total_pis=Decimal("0.17"),
            total_base_cofins=Decimal("10.00"),
            total_cofins=Decimal("0.76"),
            total_base_ipi=Decimal("0.00"),
            total_ipi=Decimal("0.00"),
            total_tributos=Decimal("2.73"),
            itens=(item,),
        )

        self.assertEqual(len(dados.itens), 1)
        self.assertIsNone(dados.numero)