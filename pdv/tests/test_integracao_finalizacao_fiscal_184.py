from types import SimpleNamespace
from unittest.mock import patch

from django.test import TestCase

from pdv.choices import (
    StatusOperacaoVenda,
    TipoEmissaoVenda,
)
from pdv.services.vendas.finalizacao import finalizar_venda


class VendaManagerFake:
    def __init__(self, venda):
        self.venda = venda

    def select_for_update(self):
        return self

    def select_related(self, *args):
        return self

    def get(self, **kwargs):
        return self.venda


def venda_fake(tipo_emissao):
    return SimpleNamespace(
        pk=1,
        status="aberta",
        tipo_emissao=tipo_emissao,
        operador=SimpleNamespace(pk=10),
    )


class IntegracaoFinalizacaoFiscal184Tests(TestCase):
    @patch(
        "pdv.services.vendas.finalizacao."
        "registrar_auditoria_finalizacao_venda"
    )
    @patch(
        "pdv.services.vendas.finalizacao._finalizar_modelo"
    )
    @patch(
        "pdv.services.vendas.finalizacao."
        "registrar_movimentacao_caixa_venda"
    )
    @patch(
        "pdv.services.vendas.finalizacao._confirmar_reservas"
    )
    @patch(
        "pdv.services.vendas.finalizacao."
        "preparar_e_persistir_snapshot_fiscal_venda"
    )
    @patch(
        "pdv.services.vendas.finalizacao."
        "validar_venda_para_finalizacao"
    )
    @patch(
        "pdv.services.vendas.finalizacao."
        "_associar_cliente_consumidor"
    )
    def test_nao_fiscal_nao_chama_pipeline(
        self,
        associar,
        validar,
        fiscal,
        estoque,
        caixa,
        finalizar,
        auditoria,
    ):
        venda = venda_fake(
            TipoEmissaoVenda.NAO_FISCAL
        )

        caixa.return_value = SimpleNamespace(pk=20)

        with patch(
            "pdv.services.vendas.finalizacao.Venda.objects",
            VendaManagerFake(venda),
        ):
            retorno = finalizar_venda(venda=venda)

        self.assertIs(retorno, venda)

        validar.assert_called_once_with(
            venda=venda,
            permitir_fiscal=False,
        )

        fiscal.assert_not_called()
        estoque.assert_called_once()
        caixa.assert_called_once()
        finalizar.assert_called_once()
        auditoria.assert_called_once()

    @patch(
        "pdv.services.vendas.finalizacao."
        "registrar_auditoria_finalizacao_venda"
    )
    @patch(
        "pdv.services.vendas.finalizacao._finalizar_modelo"
    )
    @patch(
        "pdv.services.vendas.finalizacao."
        "registrar_movimentacao_caixa_venda"
    )
    @patch(
        "pdv.services.vendas.finalizacao._confirmar_reservas"
    )
    @patch(
        "pdv.services.vendas.finalizacao."
        "preparar_e_persistir_snapshot_fiscal_venda"
    )
    @patch(
        "pdv.services.vendas.finalizacao."
        "validar_venda_para_finalizacao"
    )
    @patch(
        "pdv.services.vendas.finalizacao."
        "_associar_cliente_consumidor"
    )
    def test_fiscal_executa_pipeline_antes_de_estoque(
        self,
        associar,
        validar,
        fiscal,
        estoque,
        caixa,
        finalizar,
        auditoria,
    ):
        venda = venda_fake(
            TipoEmissaoVenda.FISCAL
        )

        caixa.return_value = SimpleNamespace(pk=20)

        ordem = []

        fiscal.side_effect = lambda **kwargs: ordem.append(
            "fiscal"
        )
        estoque.side_effect = lambda **kwargs: ordem.append(
            "estoque"
        )
        caixa.side_effect = lambda **kwargs: (
            ordem.append("caixa")
            or SimpleNamespace(pk=20)
        )

        with patch(
            "pdv.services.vendas.finalizacao.Venda.objects",
            VendaManagerFake(venda),
        ):
            finalizar_venda(venda=venda)

        validar.assert_called_once_with(
            venda=venda,
            permitir_fiscal=True,
        )

        self.assertEqual(
            ordem[:3],
            ["fiscal", "estoque", "caixa"],
        )

    @patch(
        "pdv.services.vendas.finalizacao."
        "registrar_movimentacao_caixa_venda"
    )
    @patch(
        "pdv.services.vendas.finalizacao._confirmar_reservas"
    )
    @patch(
        "pdv.services.vendas.finalizacao."
        "preparar_e_persistir_snapshot_fiscal_venda"
    )
    @patch(
        "pdv.services.vendas.finalizacao."
        "validar_venda_para_finalizacao"
    )
    @patch(
        "pdv.services.vendas.finalizacao."
        "_associar_cliente_consumidor"
    )
    def test_falha_fiscal_impede_estoque_e_caixa(
        self,
        associar,
        validar,
        fiscal,
        estoque,
        caixa,
    ):
        venda = venda_fake(
            TipoEmissaoVenda.FISCAL
        )

        fiscal.side_effect = RuntimeError(
            "falha fiscal controlada"
        )

        with patch(
            "pdv.services.vendas.finalizacao.Venda.objects",
            VendaManagerFake(venda),
        ):
            with self.assertRaises(RuntimeError):
                finalizar_venda(venda=venda)

        estoque.assert_not_called()
        caixa.assert_not_called()