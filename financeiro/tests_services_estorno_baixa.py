from datetime import date
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

from empresas.models import Matriz
from financeiro.models import BaixaFinanceira, ParcelaFinanceira, TituloFinanceiro
from financeiro.services import criar_titulo_financeiro, registrar_baixa_financeira


class EstornarBaixaFinanceiraContratoTests(TestCase):
    def setUp(self):
        self.matriz = Matriz.objects.create(nome="Matriz Estorno Teste")
        self.titulo = criar_titulo_financeiro(
            matriz=self.matriz,
            loja=None,
            natureza=TituloFinanceiro.Natureza.RECEBER,
            origem_tipo="MANUAL",
            origem_id="manual-estorno-001",
            chave_idempotencia="titulo-estorno-001",
            descricao="Titulo para estorno",
            data_emissao=date(2026, 9, 14),
            parcelas=[
                {"numero": 1, "vencimento": date(2026, 10, 14), "valor": Decimal("100.00")},
            ],
        )
        self.parcela = self.titulo.parcelas.get(numero=1)
        self.baixa = registrar_baixa_financeira(
            parcela=self.parcela,
            valor=Decimal("40.00"),
            data=date(2026, 9, 14),
            chave_idempotencia="baixa-estorno-base-001",
            observacao="Baixa original",
        )

    def _estornar(self, **overrides):
        from financeiro.services import estornar_baixa_financeira
        dados = {
            "baixa": self.baixa,
            "valor": Decimal("40.00"),
            "data": date(2026, 9, 15),
            "chave_idempotencia": "estorno-001",
            "observacao": "Estorno da baixa",
        }
        dados.update(overrides)
        return estornar_baixa_financeira(**dados)

    def test_servico_publico_deve_existir(self):
        from financeiro.services import estornar_baixa_financeira
        self.assertTrue(callable(estornar_baixa_financeira))

    def test_estorno_total_deve_criar_evento_sem_apagar_baixa(self):
        estorno = self._estornar()
        self.assertEqual(estorno.tipo, BaixaFinanceira.Tipo.ESTORNO)
        self.assertEqual(estorno.valor, Decimal("40.00"))
        self.assertTrue(BaixaFinanceira.objects.filter(pk=self.baixa.pk).exists())
        self.assertEqual(BaixaFinanceira.objects.count(), 2)

    def test_estorno_total_deve_reabrir_parcela_e_titulo(self):
        self._estornar()
        self.parcela.refresh_from_db()
        self.titulo.refresh_from_db()
        self.assertEqual(self.parcela.status, ParcelaFinanceira.Status.ABERTO)
        self.assertEqual(self.titulo.status, TituloFinanceiro.Status.ABERTO)

    def test_estorno_parcial_deve_manter_status_parcial(self):
        self._estornar(valor=Decimal("10.00"))
        self.parcela.refresh_from_db()
        self.titulo.refresh_from_db()
        self.assertEqual(self.parcela.status, ParcelaFinanceira.Status.PARCIAL)
        self.assertEqual(self.titulo.status, TituloFinanceiro.Status.PARCIAL)

    def test_estorno_acima_do_total_baixado_deve_falhar(self):
        with self.assertRaises(ValidationError):
            self._estornar(valor=Decimal("40.01"))
        self.assertEqual(BaixaFinanceira.objects.filter(tipo=BaixaFinanceira.Tipo.ESTORNO).count(), 0)

    def test_estorno_zero_deve_falhar(self):
        with self.assertRaises(ValidationError):
            self._estornar(valor=Decimal("0.00"))
        self.assertEqual(BaixaFinanceira.objects.filter(tipo=BaixaFinanceira.Tipo.ESTORNO).count(), 0)

    def test_repeticao_mesma_chave_deve_ser_idempotente(self):
        primeiro = self._estornar()
        segundo = self._estornar()
        self.assertEqual(primeiro.pk, segundo.pk)
        self.assertEqual(BaixaFinanceira.objects.filter(tipo=BaixaFinanceira.Tipo.ESTORNO).count(), 1)

    def test_mesma_chave_com_valor_diferente_deve_rejeitar(self):
        self._estornar()
        with self.assertRaises(ValidationError):
            self._estornar(valor=Decimal("39.00"))