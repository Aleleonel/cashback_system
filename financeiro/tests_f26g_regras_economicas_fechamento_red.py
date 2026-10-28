from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from empresas.models import Matriz
from financeiro.models import CentroCusto, PlanoConta, TituloFinanceiro
from financeiro.services import validar_fechamento_gerencial


class F26GRegrasEconomicasFechamentoRED(TestCase):
    def setUp(self):
        self.matriz = Matriz.objects.create(nome="Matriz F26G", status="ativa")
        self.cc = CentroCusto.objects.create(
            matriz=self.matriz, codigo="CC-F26G", nome="Centro F26G"
        )
        self.plano_sem_dre = PlanoConta.objects.create(
            matriz=self.matriz,
            codigo="F26G-001",
            nome="Despesa sem classificacao DRE",
            tipo=PlanoConta.Tipo.ANALITICA,
            natureza=PlanoConta.Natureza.DESPESA,
            aceita_lancamento=True,
        )

    def _titulo(self, *, origem, competencia=date(2026, 9, 15), plano=None, status=None):
        return TituloFinanceiro.objects.create(
            matriz=self.matriz,
            natureza=TituloFinanceiro.Natureza.PAGAR,
            origem_tipo=origem,
            origem_id=f"F26G-{origem}-{TituloFinanceiro.objects.count()+1}",
            chave_idempotencia=f"F26G-{origem}-{TituloFinanceiro.objects.count()+1}",
            plano_conta=plano,
            centro_custo=self.cc if origem in (TituloFinanceiro.OrigemTipo.MANUAL, TituloFinanceiro.OrigemTipo.AJUSTE) else None,
            descricao="F26G",
            valor_original=Decimal("100.00"),
            valor_bruto=Decimal("100.00"),
            data_competencia=competencia,
            data_emissao=date(2026, 9, 15),
            status=status or TituloFinanceiro.Status.ABERTO,
        )

    def _validar(self):
        return validar_fechamento_gerencial(
            matriz=self.matriz, competencia_ano=2026, competencia_mes=9
        )

    def test_manual_ativo_sem_classificacao_dre_e_pendencia_bloqueante(self):
        self._titulo(origem=TituloFinanceiro.OrigemTipo.MANUAL, plano=self.plano_sem_dre)
        r = self._validar()
        item = next(i for i in r["itens"] if i["codigo"] == "LANCAMENTOS_ECONOMICOS_CLASSIFICADOS_DRE")
        self.assertEqual(item["status"], "PENDENTE")
        self.assertTrue(item["bloqueante"])
        self.assertFalse(r["valido"])

    def test_manual_cancelado_sem_classificacao_nao_bloqueia(self):
        self._titulo(
            origem=TituloFinanceiro.OrigemTipo.MANUAL,
            plano=self.plano_sem_dre,
            status=TituloFinanceiro.Status.CANCELADO,
        )
        r = self._validar()
        item = next(i for i in r["itens"] if i["codigo"] == "LANCAMENTOS_ECONOMICOS_CLASSIFICADOS_DRE")
        self.assertEqual(item["status"], "OK")

    def test_compra_recebimento_sem_plano_competencia_cc_nao_bloqueia(self):
        self._titulo(
            origem=TituloFinanceiro.OrigemTipo.COMPRA_RECEBIMENTO,
            competencia=None,
            plano=None,
        )
        self.assertTrue(self._validar()["valido"])

    def test_venda_pagamento_sem_plano_competencia_cc_nao_bloqueia(self):
        self._titulo(
            origem=TituloFinanceiro.OrigemTipo.VENDA_PAGAMENTO,
            competencia=None,
            plano=None,
        )
        self.assertTrue(self._validar()["valido"])

    def test_titulo_financeiro_comissao_nao_e_fonte_economica_bloqueante(self):
        self._titulo(
            origem=TituloFinanceiro.OrigemTipo.COMISSAO,
            competencia=None,
            plano=None,
        )
        self.assertTrue(self._validar()["valido"])

    def test_checklist_expoe_item_de_comissao_mensal(self):
        r = self._validar()
        item = next(i for i in r["itens"] if i["codigo"] == "COMISSAO_MENSAL")
        self.assertIn(item["status"], {"OK", "AVISO"})
        self.assertFalse(item["bloqueante"])

    def test_checklist_expoe_item_de_integridade_cmv(self):
        r = self._validar()
        item = next(i for i in r["itens"] if i["codigo"] == "INTEGRIDADE_CMV_SNAPSHOT")
        self.assertIn(item["status"], {"OK", "AVISO"})
        self.assertFalse(item["bloqueante"])