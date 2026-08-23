from dataclasses import MISSING
from decimal import Decimal
import inspect

from django.test import SimpleTestCase

from fiscal.dto_documento_fiscal import DadosItemDocumentoFiscal
import fiscal.services_preparacao_documento_fiscal as preparacao


class ContratoICMS195F2A1Tests(SimpleTestCase):

    def test_dto_expoe_modalidade_base_icms(self):
        campo = DadosItemDocumentoFiscal.__dataclass_fields__[
            "modalidade_base_icms"
        ]

        self.assertIsNot(campo.default, MISSING)
        self.assertEqual(campo.default, "")

    def test_dto_expoe_percentual_reducao_base_icms(self):
        campo = DadosItemDocumentoFiscal.__dataclass_fields__[
            "percentual_reducao_base_icms"
        ]

        self.assertIsNot(campo.default, MISSING)
        self.assertEqual(campo.default, Decimal("0"))

    def test_preparacao_define_modbc_valor_operacao(self):
        fonte = inspect.getsource(preparacao)

        self.assertIn(
            'modalidade_base_icms="3"',
            fonte,
        )

    def test_preparacao_propaga_percentual_reducao_snapshot(self):
        fonte = inspect.getsource(preparacao)

        self.assertIn(
            "item_fiscal.percentual_reducao_base_icms",
            fonte,
        )
