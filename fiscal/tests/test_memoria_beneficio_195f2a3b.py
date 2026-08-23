from decimal import Decimal
from types import SimpleNamespace

from django.test import SimpleTestCase

from fiscal.domain import EstadoSelecaoFiscal, ResultadoSelecaoFiscal
from fiscal.domain.calculo_tributario import (
    ContextoCalculoTributario,
)
from fiscal.services_motor_tributario import calcular_tributos


def _selecao_real(regra):
    return ResultadoSelecaoFiscal(
        estado=EstadoSelecaoFiscal.SELECIONADA,
        regra=regra,
        codigo_regra=regra.codigo_interno,
        prioridade=regra.prioridade,
        avisos=(),
        memoria_decisao={"teste": True},
        regras_conflitantes=(),
    )

def _regra(*, beneficio=None):
    return SimpleNamespace(
        codigo_interno="REG-TESTE",
        prioridade=1,
        beneficio_fiscal=beneficio,
        beneficio_fiscal_id=(1 if beneficio is not None else None),
        reducao_base_icms=None,
        aliquota_icms=Decimal("18"),
        aliquota_fcp=Decimal("0"),
        aliquota_pis=Decimal("0"),
        aliquota_cofins=Decimal("0"),
        aliquota_ipi=Decimal("0"),
        diferimento_icms=None,
    )


def _contexto(regra):
    return ContextoCalculoTributario(
        valor_produtos=Decimal("100.00"),
        quantidade=Decimal("1"),
        desconto=Decimal("0"),
        acrescimo=Decimal("0"),
        frete=Decimal("0"),
        seguro=Decimal("0"),
        outras_despesas=Decimal("0"),
        base_manual=None,
        percentual_reducao_manual=None,
        resultado_selecao_fiscal=_selecao_real(regra),
    )


class MemoriaBeneficio195F2A3BTests(SimpleTestCase):

    def test_memoria_preserva_codigo_legado_e_novos_campos(self):
        beneficio = SimpleNamespace(
            codigo="BEN-001",
            tipo_beneficio="desoneracao",
            descricao="Beneficio teste",
            exige_motivo_desoneracao=True,
            motivo_desoneracao_padrao="3",
        )

        resultado = calcular_tributos(
            _contexto(_regra(beneficio=beneficio))
        )

        memoria_regra = resultado.memoria_calculo["regra"]

        self.assertEqual(
            memoria_regra["beneficio_fiscal"],
            "BEN-001",
        )
        self.assertEqual(
            memoria_regra["beneficio_fiscal_tipo"],
            "desoneracao",
        )
        self.assertEqual(
            memoria_regra["beneficio_fiscal_descricao"],
            "Beneficio teste",
        )
        self.assertTrue(
            memoria_regra["beneficio_exige_motivo_desoneracao"]
        )
        self.assertEqual(
            memoria_regra["beneficio_motivo_desoneracao"],
            "3",
        )

    def test_sem_beneficio_gera_defaults_explicitos(self):
        resultado = calcular_tributos(
            _contexto(_regra(beneficio=None))
        )

        memoria_regra = resultado.memoria_calculo["regra"]

        self.assertIsNone(memoria_regra["beneficio_fiscal"])
        self.assertIsNone(
            memoria_regra["beneficio_fiscal_tipo"]
        )
        self.assertIsNone(
            memoria_regra["beneficio_fiscal_descricao"]
        )
        self.assertFalse(
            memoria_regra[
                "beneficio_exige_motivo_desoneracao"
            ]
        )
        self.assertIsNone(
            memoria_regra["beneficio_motivo_desoneracao"]
        )

    def test_motivo_e_congelado_sem_transformacao(self):
        beneficio = SimpleNamespace(
            codigo="BEN-002",
            tipo_beneficio="isencao",
            descricao="Isencao teste",
            exige_motivo_desoneracao=True,
            motivo_desoneracao_padrao=" 9 ",
        )

        resultado = calcular_tributos(
            _contexto(_regra(beneficio=beneficio))
        )

        self.assertEqual(
            resultado.memoria_calculo["regra"][
                "beneficio_motivo_desoneracao"
            ],
            " 9 ",
        )


