from datetime import date
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

from empresas.models import Matriz
from financeiro.models import BaixaFinanceira, ParcelaFinanceira, TituloFinanceiro
from financeiro.services import criar_titulo_financeiro


class RegistrarBaixaFinanceiraContratoTests(TestCase):
    def setUp(self):
        self.matriz = Matriz.objects.create(nome="Matriz Baixa Teste")
        self.titulo = criar_titulo_financeiro(
            matriz=self.matriz,
            loja=None,
            natureza=TituloFinanceiro.Natureza.RECEBER,
            origem_tipo="MANUAL",
            origem_id="manual-baixa-001",
            chave_idempotencia="titulo-baixa-001",
            descricao="Titulo para baixa",
            data_emissao=date(2026, 9, 14),
            parcelas=[
                {"numero": 1, "vencimento": date(2026, 10, 14), "valor": Decimal("100.00")},
            ],
        )
        self.parcela = self.titulo.parcelas.get(numero=1)

    def _registrar(self, **overrides):
        from financeiro.services import registrar_baixa_financeira
        dados = {
            "parcela": self.parcela,
            "valor": Decimal("40.00"),
            "data": date(2026, 9, 14),
            "chave_idempotencia": "baixa-001",
            "observacao": "Recebimento parcial",
        }
        dados.update(overrides)
        return registrar_baixa_financeira(**dados)

    def test_servico_publico_deve_existir(self):
        from financeiro.services import registrar_baixa_financeira
        self.assertTrue(callable(registrar_baixa_financeira))

    def test_baixa_parcial_deve_criar_evento_e_atualizar_status(self):
        baixa = self._registrar()
        self.assertEqual(baixa.tipo, BaixaFinanceira.Tipo.BAIXA)
        self.assertEqual(baixa.valor, Decimal("40.00"))
        self.parcela.refresh_from_db()
        self.titulo.refresh_from_db()
        self.assertEqual(self.parcela.status, ParcelaFinanceira.Status.PARCIAL)
        self.assertEqual(self.titulo.status, TituloFinanceiro.Status.PARCIAL)

    def test_baixa_total_deve_liquidar_parcela_e_titulo(self):
        self._registrar(valor=Decimal("100.00"))
        self.parcela.refresh_from_db()
        self.titulo.refresh_from_db()
        self.assertEqual(self.parcela.status, ParcelaFinanceira.Status.LIQUIDADO)
        self.assertEqual(self.titulo.status, TituloFinanceiro.Status.LIQUIDADO)

    def test_baixa_acima_do_saldo_deve_falhar_sem_evento(self):
        with self.assertRaises(ValidationError):
            self._registrar(valor=Decimal("100.01"))
        self.assertEqual(BaixaFinanceira.objects.count(), 0)

    def test_baixa_zero_deve_falhar_sem_evento(self):
        with self.assertRaises(ValidationError):
            self._registrar(valor=Decimal("0.00"))
        self.assertEqual(BaixaFinanceira.objects.count(), 0)

    def test_repeticao_mesma_chave_deve_ser_idempotente(self):
        primeira = self._registrar()
        segunda = self._registrar()
        self.assertEqual(primeira.pk, segunda.pk)
        self.assertEqual(BaixaFinanceira.objects.count(), 1)

    def test_mesma_chave_com_valor_diferente_deve_rejeitar(self):
        self._registrar()
        with self.assertRaises(ValidationError):
            self._registrar(valor=Decimal("41.00"))
        self.assertEqual(BaixaFinanceira.objects.count(), 1)