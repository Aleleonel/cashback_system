from datetime import date
from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase

from fiscal.domain.selecao_fiscal import (
    ContextoSelecaoFiscal,
    EstadoSelecaoFiscal,
)
from produtos.services.fiscal import (
    StatusProdutoFiscal,
    resolver_produto_fiscal,
)


def objeto(**dados):
    return SimpleNamespace(**dados)


class ResolverProdutoFiscalTests(SimpleTestCase):
    def contexto(self, **extras):
        dados = {
            "data_operacao": date.today(),
            "regime_tributario": "normal",
            "tipo_operacao": "saida",
            "finalidade_operacao": "venda",
            "uf_origem": "SP",
            "uf_destino": "SP",
            "matriz": None,
            "loja": None,
            "contribuinte_icms": True,
            "consumidor_final": False,
            "ncm": None,
            "cest": None,
        }
        dados.update(extras)
        return ContextoSelecaoFiscal(**dados)

    def produto(self, **extras):
        dados = {
            "regra_fiscal_padrao": None,
            "origem_mercadoria": objeto(codigo="0"),
            "ncm_fiscal": objeto(codigo="21069090"),
            "ncm": "",
            "cest": None,
            "cst_icms": objeto(codigo="00"),
            "csosn": None,
            "cst_pis": objeto(codigo="01"),
            "cst_cofins": objeto(codigo="01"),
            "cst_ipi": objeto(codigo="50"),
            "beneficio_fiscal": None,
        }
        dados.update(extras)
        return objeto(**dados)

    def regra(self, **extras):
        dados = {
            "codigo_interno": "REG-001",
            "ncm": None,
            "cest": None,
            "cst_icms": objeto(codigo="20"),
            "csosn": None,
            "cst_pis": objeto(codigo="02"),
            "cst_cofins": objeto(codigo="02"),
            "cst_ipi": objeto(codigo="51"),
            "beneficio_fiscal": objeto(codigo="BEN-01"),
            "observacoes": "Regra de teste.",
        }
        dados.update(extras)
        return objeto(**dados)

    @patch("produtos.services.fiscal.resolver_produto_fiscal.selecionar_regra")
    def test_regra_direta_do_produto_tem_precedencia(self, selecionar):
        regra = self.regra()
        produto = self.produto(regra_fiscal_padrao=regra)

        resolvido = resolver_produto_fiscal(
            produto=produto,
            contexto=self.contexto(),
        )

        selecionar.assert_not_called()
        self.assertIs(resolvido.regra, regra)
        self.assertIn("diretamente", resolvido.motivo_selecao)

    def test_campos_do_produto_substituem_campos_da_regra(self):
        regra = self.regra()
        produto = self.produto(regra_fiscal_padrao=regra)

        resolvido = resolver_produto_fiscal(
            produto=produto,
            contexto=self.contexto(),
        )

        self.assertEqual(resolvido.cst_icms.codigo, "00")
        self.assertEqual(resolvido.cst_pis.codigo, "01")
        self.assertEqual(resolvido.cst_cofins.codigo, "01")
        self.assertEqual(resolvido.cst_ipi.codigo, "50")

    def test_campos_vazios_do_produto_herdam_da_regra(self):
        regra = self.regra()
        produto = self.produto(
            regra_fiscal_padrao=regra,
            cst_icms=None,
            cst_pis=None,
            cst_cofins=None,
            cst_ipi=None,
            beneficio_fiscal=None,
        )

        resolvido = resolver_produto_fiscal(
            produto=produto,
            contexto=self.contexto(),
        )

        self.assertEqual(resolvido.cst_icms.codigo, "20")
        self.assertEqual(resolvido.cst_pis.codigo, "02")
        self.assertEqual(resolvido.beneficio.codigo, "BEN-01")

    @patch("produtos.services.fiscal.resolver_produto_fiscal.selecionar_regra")
    def test_motor_recebe_ncm_e_cest_do_produto(self, selecionar):
        regra = self.regra()
        resultado = objeto(
            estado=EstadoSelecaoFiscal.SELECIONADA,
            regra=regra,
            memoria_decisao={"regra_selecionada": "REG-001"},
            regras_conflitantes=(),
            avisos=(),
        )
        selecionar.return_value = resultado

        ncm = objeto(codigo="21069090")
        cest = objeto(codigo="17.123.00")
        produto = self.produto(ncm_fiscal=ncm, cest=cest)

        resolver_produto_fiscal(
            produto=produto,
            contexto=self.contexto(),
        )

        contexto_recebido = selecionar.call_args.args[0]
        self.assertIs(contexto_recebido.ncm, ncm)
        self.assertIs(contexto_recebido.cest, cest)

    @patch("produtos.services.fiscal.resolver_produto_fiscal.selecionar_regra")
    def test_sem_regra_retorna_status_estruturado(self, selecionar):
        selecionar.return_value = objeto(
            estado=EstadoSelecaoFiscal.NAO_ENCONTRADA,
            regra=None,
            memoria_decisao={"etapa": "sem_regra"},
            regras_conflitantes=(),
            avisos=("Nenhuma regra encontrada.",),
        )

        resolvido = resolver_produto_fiscal(
            produto=self.produto(),
            contexto=self.contexto(),
        )

        self.assertEqual(resolvido.status, StatusProdutoFiscal.SEM_REGRA)
        self.assertIsNone(resolvido.regra)
        self.assertIn("Nenhuma regra encontrada.", resolvido.alertas)

    @patch("produtos.services.fiscal.resolver_produto_fiscal.selecionar_regra")
    def test_ambiguidade_retorna_status_e_conflitos(self, selecionar):
        selecionar.return_value = objeto(
            estado=EstadoSelecaoFiscal.AMBIGUA,
            regra=None,
            memoria_decisao={"regras_conflitantes": ["REG-A", "REG-B"]},
            regras_conflitantes=("REG-A", "REG-B"),
            avisos=(),
        )

        resolvido = resolver_produto_fiscal(
            produto=self.produto(),
            contexto=self.contexto(),
        )

        self.assertEqual(resolvido.status, StatusProdutoFiscal.AMBIGUA)
        self.assertTrue(
            any("REG-A" in alerta for alerta in resolvido.alertas)
        )

    def test_simples_nacional_utiliza_csosn(self):
        regra = self.regra(
            cst_icms=objeto(codigo="00"),
            csosn=objeto(codigo="102"),
        )
        produto = self.produto(
            regra_fiscal_padrao=regra,
            cst_icms=None,
            csosn=None,
        )

        resolvido = resolver_produto_fiscal(
            produto=produto,
            contexto=self.contexto(regime_tributario="simples"),
        )

        self.assertIsNone(resolvido.cst_icms)
        self.assertEqual(resolvido.csosn.codigo, "102")
