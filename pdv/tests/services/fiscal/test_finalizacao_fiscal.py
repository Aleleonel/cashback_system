from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.core.exceptions import ValidationError
from django.test import SimpleTestCase

from fiscal.domain import (
    EstadoSelecaoFiscal,
    ResultadoSelecaoFiscal,
)
from pdv.choices import TipoEmissaoVenda
from pdv.services.fiscal.finalizacao_fiscal import (
    preparar_e_persistir_snapshot_fiscal_venda,
)


class QueryItensFake:
    def __init__(self, itens):
        self.itens = itens

    def filter(self, **kwargs):
        return self

    def select_related(self, *args):
        return self

    def order_by(self, *args):
        return self

    def __iter__(self):
        return iter(self.itens)


class VendaFiscalFake:
    def __init__(self, itens):
        self.tipo_emissao = TipoEmissaoVenda.FISCAL
        self.matriz_id = 1
        self.loja_id = 2
        self.matriz = SimpleNamespace(pk=1)
        self.loja = SimpleNamespace(pk=2, matriz_id=1)
        self.uf_destino = "SP"
        self.itens = QueryItensFake(itens)


def item_fake(sequencia=1):
    return SimpleNamespace(
        pk=10 + sequencia,
        venda_id=100,
        sequencia=sequencia,
        produto=SimpleNamespace(pk=200 + sequencia),
        quantidade=Decimal("2.000"),
        preco_unitario=Decimal("50.00"),
        subtotal=Decimal("100.00"),
        desconto=Decimal("5.00"),
        acrescimo=Decimal("1.00"),
        total=Decimal("96.00"),
    )


class FinalizacaoFiscalOrquestradorTests(SimpleTestCase):
    def test_rejeita_venda_nao_fiscal(self):
        venda = VendaFiscalFake([item_fake()])
        venda.tipo_emissao = TipoEmissaoVenda.NAO_FISCAL

        with self.assertRaises(ValidationError):
            preparar_e_persistir_snapshot_fiscal_venda(
                venda=venda,
            )

    @patch(
        "pdv.services.fiscal.finalizacao_fiscal."
        "persistir_venda_fiscal"
    )
    @patch(
        "pdv.services.fiscal.finalizacao_fiscal."
        "consolidar_dados_venda_fiscal"
    )
    @patch(
        "pdv.services.fiscal.finalizacao_fiscal."
        "persistir_item_venda_fiscal"
    )
    @patch(
        "pdv.services.fiscal.finalizacao_fiscal."
        "construir_dados_item_venda_fiscal"
    )
    @patch(
        "pdv.services.fiscal.finalizacao_fiscal."
        "calcular_tributos"
    )
    @patch(
        "pdv.services.fiscal.finalizacao_fiscal."
        "resolver_produto_fiscal"
    )
    @patch(
        "pdv.services.fiscal.finalizacao_fiscal."
        "construir_contexto_tributario"
    )
    @patch(
        "pdv.services.fiscal.finalizacao_fiscal."
        "get_configuracao_fiscal_matriz"
    )
    def test_orquestra_todos_os_itens_e_consolida(
        self,
        get_configuracao,
        construir_contexto,
        resolver_produto,
        calcular,
        construir_dados,
        persistir_item,
        consolidar,
        persistir_venda,
    ):
        itens = [item_fake(1), item_fake(2)]
        venda = VendaFiscalFake(itens)

        get_configuracao.return_value = SimpleNamespace(
            pk=99,
            pronta_para_operacao=True,
        )

        contexto = SimpleNamespace(
            regime_tributario="normal",
            uf_origem="SP",
            uf_destino="SP",
            tipo_operacao="saida",
            finalidade_operacao="venda",
            contribuinte_icms=True,
            consumidor_final=True,
        )
        construir_contexto.return_value = contexto

        regra = SimpleNamespace(
            codigo_interno="REG-TESTE",
        )

        resultado_selecao = ResultadoSelecaoFiscal(
            estado=EstadoSelecaoFiscal.SELECIONADA,
            regra=regra,
            codigo_regra="REG-TESTE",
            prioridade=1,
            criterios_atendidos=("teste",),
            candidatas_avaliadas=1,
            memoria_decisao={"origem": "teste_184c"},
        )

        resolver_produto.return_value = SimpleNamespace(
            valido=True,
            alertas=(),
            resultado_selecao_fiscal=resultado_selecao,
        )

        calcular.return_value = SimpleNamespace()
        construir_dados.side_effect = ["dados-1", "dados-2"]

        snapshots = [
            SimpleNamespace(
                base_operacao=Decimal("100"),
                base_icms=Decimal("100"),
                valor_icms=Decimal("18"),
                valor_fcp=Decimal("0"),
                base_pis=Decimal("100"),
                valor_pis=Decimal("1.65"),
                base_cofins=Decimal("100"),
                valor_cofins=Decimal("7.60"),
                base_ipi=Decimal("0"),
                valor_ipi=Decimal("0"),
                valor_total_tributos=Decimal("27.25"),
            ),
            SimpleNamespace(
                base_operacao=Decimal("50"),
                base_icms=Decimal("50"),
                valor_icms=Decimal("9"),
                valor_fcp=Decimal("0"),
                base_pis=Decimal("50"),
                valor_pis=Decimal("0.82"),
                base_cofins=Decimal("50"),
                valor_cofins=Decimal("3.80"),
                base_ipi=Decimal("0"),
                valor_ipi=Decimal("0"),
                valor_total_tributos=Decimal("13.62"),
            ),
        ]

        persistir_item.side_effect = snapshots
        consolidar.return_value = "dados-venda"
        persistir_venda.return_value = "snapshot-venda"

        retorno = preparar_e_persistir_snapshot_fiscal_venda(
            venda=venda,
        )

        self.assertEqual(retorno, "snapshot-venda")
        self.assertEqual(resolver_produto.call_count, 2)
        self.assertEqual(calcular.call_count, 2)
        self.assertEqual(construir_dados.call_count, 2)
        self.assertEqual(persistir_item.call_count, 2)

        consolidar.assert_called_once()
        persistir_venda.assert_called_once_with(
            venda=venda,
            dados="dados-venda",
        )

    @patch(
        "pdv.services.fiscal.finalizacao_fiscal."
        "get_configuracao_fiscal_matriz"
    )
    def test_configuracao_ausente_bloqueia(self, get_configuracao):
        venda = VendaFiscalFake([item_fake()])
        get_configuracao.return_value = None

        with self.assertRaises(ValidationError) as erro:
            preparar_e_persistir_snapshot_fiscal_venda(
                venda=venda,
            )

        self.assertIn(
            "configuracao_fiscal",
            erro.exception.message_dict,
        )