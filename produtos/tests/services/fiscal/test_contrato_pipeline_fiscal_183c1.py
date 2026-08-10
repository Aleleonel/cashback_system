from datetime import date
from types import SimpleNamespace

from django.test import SimpleTestCase

from fiscal.domain import (
    ContextoSelecaoFiscal,
    EstadoSelecaoFiscal,
)
from produtos.services.fiscal.resolver_produto_fiscal import (
    resolver_produto_fiscal,
)


class ContratoResolverFiscal183C1Tests(SimpleTestCase):
    def test_regra_direta_expoe_resultado_selecao_fiscal(self):
        regra = SimpleNamespace(
            codigo_interno="REG-DIRETA",
            prioridade=10,
            ncm=None,
            cest=None,
            cst_icms="00",
            csosn=None,
            cst_pis="01",
            cst_cofins="01",
            cst_ipi="50",
            beneficio_fiscal=None,
            observacoes="",
        )

        produto = SimpleNamespace(
            regra_fiscal_padrao=regra,
            origem_mercadoria="0",
            ncm_fiscal="21069090",
            ncm=None,
            cest=None,
            cst_icms="00",
            csosn=None,
            cst_pis="01",
            cst_cofins="01",
            cst_ipi="50",
            beneficio_fiscal=None,
        )

        contexto = ContextoSelecaoFiscal(
            data_operacao=date.today(),
            regime_tributario="normal",
            tipo_operacao="saida",
            finalidade_operacao="venda",
            uf_origem="SP",
            uf_destino="SP",
        )

        resolvido = resolver_produto_fiscal(
            produto=produto,
            contexto=contexto,
        )

        self.assertTrue(resolvido.valido)
        self.assertIsNotNone(
            resolvido.resultado_selecao_fiscal
        )
        self.assertEqual(
            resolvido.resultado_selecao_fiscal.estado,
            EstadoSelecaoFiscal.SELECIONADA,
        )
        self.assertIs(
            resolvido.resultado_selecao_fiscal.regra,
            regra,
        )
        self.assertEqual(
            resolvido.resultado_selecao_fiscal.codigo_regra,
            "REG-DIRETA",
        )
        self.assertEqual(
            resolvido.resultado_selecao_fiscal.memoria_decisao[
                "origem"
            ],
            "regra_fiscal_padrao",
        )