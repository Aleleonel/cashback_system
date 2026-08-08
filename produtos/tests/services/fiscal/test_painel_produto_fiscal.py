from types import SimpleNamespace
from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.test import SimpleTestCase

from produtos.services.fiscal.painel_produto_fiscal import (
    STATUS_CONTEXTO_INCOMPLETO,
    montar_painel_fiscal_produto,
)
from produtos.services.fiscal.resolver_produto_fiscal import (
    StatusProdutoFiscal,
)


def objeto(**kwargs):
    return SimpleNamespace(**kwargs)


class PainelFiscalProdutoTests(SimpleTestCase):
    def produto(self, **kwargs):
        dados = {
            "ncm_fiscal": "21069090",
            "ncm": "",
            "cest": "1712300",
            "origem_mercadoria": objeto(codigo="0"),
        }
        dados.update(kwargs)
        return objeto(**dados)

    def test_sem_uf_destino_retorna_contexto_incompleto(self):
        painel = montar_painel_fiscal_produto(
            produto=self.produto(),
            matriz=objeto(),
        )

        self.assertEqual(
            painel.status,
            STATUS_CONTEXTO_INCOMPLETO,
        )
        self.assertEqual(painel.ncm, "21069090")
        self.assertTrue(painel.alertas)

    @patch(
        "produtos.services.fiscal.painel_produto_fiscal."
        "construir_contexto_tributario"
    )
    def test_uf_invalida_vira_status_sem_erro_500(self, construir):
        construir.side_effect = ValidationError("UF invalida.")

        painel = montar_painel_fiscal_produto(
            produto=self.produto(),
            matriz=objeto(),
            uf_destino="XX",
        )

        self.assertEqual(
            painel.status,
            StatusProdutoFiscal.CONTEXTO_INVALIDO.value,
        )
        self.assertTrue(painel.alertas)

    @patch(
        "produtos.services.fiscal.painel_produto_fiscal."
        "resolver_produto_fiscal"
    )
    @patch(
        "produtos.services.fiscal.painel_produto_fiscal."
        "construir_contexto_tributario"
    )
    def test_resultado_valido_e_convertido_para_dto(
        self,
        construir,
        resolver,
    ):
        construir.return_value = objeto(
            uf_destino="RJ",
            uf_origem="SP",
            regime_tributario="normal",
        )
        resolver.return_value = objeto(
            status=StatusProdutoFiscal.VALIDA,
            regra=objeto(codigo="REG-001"),
            motivo_selecao=(
                "Regra fiscal selecionada pelo Motor de Selecao."
            ),
            origem=objeto(codigo="0"),
            ncm=objeto(codigo="21069090"),
            cest=objeto(codigo="1712300"),
            cst_icms=objeto(codigo="00"),
            csosn=None,
            cst_pis=objeto(codigo="01"),
            cst_cofins=objeto(codigo="01"),
            cst_ipi=objeto(codigo="50"),
            beneficio=None,
            observacoes=(),
            alertas=(),
        )

        painel = montar_painel_fiscal_produto(
            produto=self.produto(),
            matriz=objeto(),
            uf_destino="rj",
        )

        self.assertEqual(painel.status, "valida")
        self.assertEqual(painel.uf_destino, "RJ")
        self.assertEqual(painel.regra, "REG-001")
        self.assertEqual(
            painel.origem_regra,
            "Regra selecionada pelo Motor",
        )
        self.assertEqual(painel.cst_icms, "00")

    @patch(
        "produtos.services.fiscal.painel_produto_fiscal."
        "resolver_produto_fiscal"
    )
    @patch(
        "produtos.services.fiscal.painel_produto_fiscal."
        "construir_contexto_tributario"
    )
    def test_regra_direta_e_identificada(
        self,
        construir,
        resolver,
    ):
        construir.return_value = objeto(
            uf_destino="SP",
            uf_origem="SP",
            regime_tributario="simples",
        )
        resolver.return_value = objeto(
            status=StatusProdutoFiscal.VALIDA,
            regra=objeto(codigo="DIRETA"),
            motivo_selecao=(
                "Regra fiscal vinculada diretamente ao produto."
            ),
            origem=None,
            ncm=None,
            cest=None,
            cst_icms=None,
            csosn=objeto(codigo="102"),
            cst_pis=None,
            cst_cofins=None,
            cst_ipi=None,
            beneficio=None,
            observacoes=(),
            alertas=(),
        )

        painel = montar_painel_fiscal_produto(
            produto=self.produto(),
            matriz=objeto(),
            uf_destino="SP",
        )

        self.assertEqual(
            painel.origem_regra,
            "Regra vinculada ao Produto",
        )
        self.assertEqual(painel.csosn, "102")