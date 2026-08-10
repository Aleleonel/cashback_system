from decimal import Decimal
from types import SimpleNamespace

from django.core.exceptions import ValidationError
from django.test import SimpleTestCase

from pdv.services.fiscal.snapshot_venda import (
    DadosItemVendaFiscal,
    consolidar_dados_venda_fiscal,
    construir_dados_item_venda_fiscal,
)


class ResultadoFake:
    calculado = True
    erros = ()

    def __init__(self):
        self.regra = SimpleNamespace(
            pk=10,
            codigo_interno="REG-001",
            descricao="Regra teste",
            cfop="5102",
            cst_icms="00",
            csosn="",
            cst_pis="01",
            cst_cofins="01",
            cst_ipi="50",
            beneficio_fiscal=None,
            aliquota_icms=Decimal("18"),
            aliquota_fcp=Decimal("2"),
            aliquota_pis=Decimal("1.65"),
            aliquota_cofins=Decimal("7.60"),
            aliquota_ipi=Decimal("5"),
            reducao_base_icms=Decimal("10"),
            diferimento_icms=Decimal("20"),
        )

        self.base_operacao = Decimal("100.00")
        self.base_icms = Decimal("90.00")
        self.valor_icms_bruto = Decimal("16.20")
        self.valor_icms_diferido = Decimal("3.24")
        self.valor_icms = Decimal("12.96")
        self.base_fcp = Decimal("90.00")
        self.valor_fcp = Decimal("1.80")
        self.base_pis = Decimal("100.00")
        self.valor_pis = Decimal("1.65")
        self.base_cofins = Decimal("100.00")
        self.valor_cofins = Decimal("7.60")
        self.base_ipi = Decimal("100.00")
        self.valor_ipi = Decimal("5.00")
        self.valor_total_tributos = Decimal("29.01")

        self.memoria_calculo = {
            "reducao_base_icms": "12.5000",
            "tributos": {
                "icms": {"aliquota": "18.0000"},
                "fcp": {"aliquota": "2.0000"},
                "pis": {"aliquota": "1.6500"},
                "cofins": {"aliquota": "7.6000"},
                "ipi": {"aliquota": "5.0000"},
            },
            "diferimento": {
                "percentual": "15.0000",
            },
        }


def item_fake():
    return SimpleNamespace(
        quantidade=Decimal("2.000"),
        preco_unitario=Decimal("50.00"),
        subtotal=Decimal("100.00"),
        desconto=Decimal("5.00"),
        acrescimo=Decimal("1.00"),
    )


def contexto_tributario_fake():
    return SimpleNamespace(
        regime_tributario="normal",
        uf_origem="SP",
        uf_destino="RJ",
        tipo_operacao="saida",
        finalidade_operacao="venda",
        contribuinte_icms=True,
        consumidor_final=False,
    )


def contexto_calculo_fake():
    return SimpleNamespace(
        frete=Decimal("2.00"),
        seguro=Decimal("1.00"),
        outras_despesas=Decimal("3.00"),
    )


def produto_fiscal_fake():
    return SimpleNamespace(
        origem_mercadoria="0",
        ncm=SimpleNamespace(
            codigo="21069090",
            descricao="NCM teste",
        ),
        cest=SimpleNamespace(
            codigo="2806100",
            descricao="CEST teste",
        ),
    )


class ConstruirDadosItemVendaFiscalTests(SimpleTestCase):
    def construir(self, resultado=None):
        return construir_dados_item_venda_fiscal(
            item_venda=item_fake(),
            contexto_tributario=contexto_tributario_fake(),
            contexto_calculo=contexto_calculo_fake(),
            produto_fiscal=produto_fiscal_fake(),
            resultado_calculo=resultado or ResultadoFake(),
            configuracao_fiscal_id_original=99,
        )

    def test_copia_contexto_e_valores_comerciais(self):
        dados = self.construir()

        self.assertEqual(dados.quantidade, Decimal("2.000"))
        self.assertEqual(dados.valor_unitario, Decimal("50.00"))
        self.assertEqual(dados.valor_produtos, Decimal("100.00"))
        self.assertEqual(dados.desconto, Decimal("5.00"))
        self.assertEqual(dados.acrescimo, Decimal("1.00"))
        self.assertEqual(dados.frete, Decimal("2.00"))
        self.assertEqual(dados.seguro, Decimal("1.00"))
        self.assertEqual(dados.outras_despesas, Decimal("3.00"))
        self.assertEqual(dados.uf_origem, "SP")
        self.assertEqual(dados.uf_destino, "RJ")

    def test_copia_classificacao_fiscal(self):
        dados = self.construir()

        self.assertEqual(dados.ncm_codigo, "21069090")
        self.assertEqual(dados.cest_codigo, "2806100")
        self.assertEqual(dados.cfop_codigo, "5102")
        self.assertEqual(dados.cst_icms_codigo, "00")
        self.assertEqual(dados.cst_pis_codigo, "01")
        self.assertEqual(dados.cst_cofins_codigo, "01")
        self.assertEqual(dados.cst_ipi_codigo, "50")
        self.assertEqual(dados.regra_fiscal_codigo, "REG-001")

    def test_copia_valores_calculados_sem_recalcular(self):
        dados = self.construir()

        self.assertEqual(dados.base_operacao, Decimal("100.00"))
        self.assertEqual(dados.base_icms, Decimal("90.00"))
        self.assertEqual(dados.valor_icms_bruto, Decimal("16.20"))
        self.assertEqual(dados.valor_icms_diferido, Decimal("3.24"))
        self.assertEqual(dados.valor_icms, Decimal("12.96"))
        self.assertEqual(dados.valor_fcp, Decimal("1.80"))
        self.assertEqual(dados.valor_pis, Decimal("1.65"))
        self.assertEqual(dados.valor_cofins, Decimal("7.60"))
        self.assertEqual(dados.valor_ipi, Decimal("5.00"))
        self.assertEqual(dados.valor_total_tributos, Decimal("29.01"))

    def test_aliquotas_vem_da_memoria_do_calculo(self):
        dados = self.construir()

        self.assertEqual(dados.aliquota_icms, Decimal("18.0000"))
        self.assertEqual(dados.aliquota_fcp, Decimal("2.0000"))
        self.assertEqual(dados.aliquota_pis, Decimal("1.6500"))
        self.assertEqual(dados.aliquota_cofins, Decimal("7.6000"))
        self.assertEqual(dados.aliquota_ipi, Decimal("5.0000"))

    def test_reducao_e_diferimento_vem_da_memoria(self):
        dados = self.construir()

        self.assertEqual(
            dados.percentual_reducao_base_icms,
            Decimal("12.5000"),
        )
        self.assertEqual(
            dados.percentual_diferimento_icms,
            Decimal("15.0000"),
        )

    def test_fallback_de_aliquota_para_regra(self):
        resultado = ResultadoFake()
        resultado.memoria_calculo["tributos"]["icms"].pop("aliquota")

        dados = self.construir(resultado=resultado)

        self.assertEqual(
            dados.aliquota_icms,
            Decimal("18"),
        )

    def test_rejeita_resultado_nao_calculado(self):
        resultado = ResultadoFake()
        resultado.calculado = False

        with self.assertRaises(ValidationError):
            self.construir(resultado=resultado)

    def test_rejeita_resultado_com_erros(self):
        resultado = ResultadoFake()
        resultado.erros = ("erro",)

        with self.assertRaises(ValidationError):
            self.construir(resultado=resultado)

    def test_rejeita_resultado_sem_regra(self):
        resultado = ResultadoFake()
        resultado.regra = None

        with self.assertRaises(ValidationError):
            self.construir(resultado=resultado)


class ConsolidarDadosVendaFiscalTests(SimpleTestCase):
    def test_soma_totais_dos_itens(self):
        base = construir_dados_item_venda_fiscal(
            item_venda=item_fake(),
            contexto_tributario=contexto_tributario_fake(),
            contexto_calculo=contexto_calculo_fake(),
            produto_fiscal=produto_fiscal_fake(),
            resultado_calculo=ResultadoFake(),
            configuracao_fiscal_id_original=99,
        )

        dados = consolidar_dados_venda_fiscal(
            venda=SimpleNamespace(),
            contexto_tributario=contexto_tributario_fake(),
            snapshots_itens=[base, base],
            configuracao_fiscal_id_original=99,
        )

        self.assertEqual(
            dados.total_base_operacao,
            Decimal("200.00"),
        )
        self.assertEqual(
            dados.total_icms,
            Decimal("25.92"),
        )
        self.assertEqual(
            dados.total_fcp,
            Decimal("3.60"),
        )
        self.assertEqual(
            dados.total_pis,
            Decimal("3.30"),
        )
        self.assertEqual(
            dados.total_cofins,
            Decimal("15.20"),
        )
        self.assertEqual(
            dados.total_ipi,
            Decimal("10.00"),
        )
        self.assertEqual(
            dados.total_tributos,
            Decimal("58.02"),
        )

    def test_preserva_contexto_tributario(self):
        base = construir_dados_item_venda_fiscal(
            item_venda=item_fake(),
            contexto_tributario=contexto_tributario_fake(),
            contexto_calculo=contexto_calculo_fake(),
            produto_fiscal=produto_fiscal_fake(),
            resultado_calculo=ResultadoFake(),
        )

        dados = consolidar_dados_venda_fiscal(
            venda=SimpleNamespace(),
            contexto_tributario=contexto_tributario_fake(),
            snapshots_itens=[base],
        )

        self.assertEqual(dados.regime_tributario, "normal")
        self.assertEqual(dados.uf_origem, "SP")
        self.assertEqual(dados.uf_destino, "RJ")
        self.assertTrue(dados.contribuinte_icms)
        self.assertFalse(dados.consumidor_final)