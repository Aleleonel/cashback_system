from datetime import date
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.test import TestCase
from empresas.models import Matriz
from financeiro.models import TituloFinanceiro, ParcelaFinanceira


class CriarTituloFinanceiroContratoTests(TestCase):
    def setUp(self):
        self.matriz = Matriz.objects.create(nome="Matriz Financeiro Teste")

    def _kwargs(self):
        return {
            "matriz": self.matriz,
            "loja": None,
            "natureza": TituloFinanceiro.Natureza.PAGAR,
            "origem_tipo": "MANUAL",
            "origem_id": "manual-001",
            "chave_idempotencia": "titulo-manual-001",
            "descricao": "Titulo teste",
            "data_emissao": date(2026, 9, 14),
            "parcelas": [
                {"numero": 1, "vencimento": date(2026, 10, 14), "valor": Decimal("60.00")},
                {"numero": 2, "vencimento": date(2026, 11, 14), "valor": Decimal("40.00")},
            ],
        }

    def test_servico_publico_deve_existir(self):
        from financeiro.services import criar_titulo_financeiro
        self.assertTrue(callable(criar_titulo_financeiro))

    def test_criacao_deve_persistir_titulo_e_parcelas(self):
        from financeiro.services import criar_titulo_financeiro
        titulo = criar_titulo_financeiro(**self._kwargs())
        self.assertEqual(titulo.valor_original, Decimal("100.00"))
        self.assertEqual(titulo.status, TituloFinanceiro.Status.ABERTO)
        self.assertEqual(titulo.parcelas.count(), 2)
        self.assertEqual(
            list(titulo.parcelas.order_by("numero").values_list("valor_original", flat=True)),
            [Decimal("60.00"), Decimal("40.00")],
        )

    def test_mesma_chave_deve_ser_idempotente_sem_duplicar(self):
        from financeiro.services import criar_titulo_financeiro
        primeiro = criar_titulo_financeiro(**self._kwargs())
        segundo = criar_titulo_financeiro(**self._kwargs())
        self.assertEqual(primeiro.pk, segundo.pk)
        self.assertEqual(TituloFinanceiro.objects.count(), 1)
        self.assertEqual(ParcelaFinanceira.objects.count(), 2)

    def test_parcelas_vazias_devem_falhar_sem_persistencia_parcial(self):
        from financeiro.services import criar_titulo_financeiro
        dados = self._kwargs()
        dados["parcelas"] = []
        with self.assertRaises(ValidationError):
            criar_titulo_financeiro(**dados)
        self.assertEqual(TituloFinanceiro.objects.count(), 0)
        self.assertEqual(ParcelaFinanceira.objects.count(), 0)

    def test_valor_zero_de_parcela_deve_falhar_atomicamente(self):
        from financeiro.services import criar_titulo_financeiro
        dados = self._kwargs()
        dados["parcelas"][1]["valor"] = Decimal("0.00")
        with self.assertRaises(ValidationError):
            criar_titulo_financeiro(**dados)
        self.assertEqual(TituloFinanceiro.objects.count(), 0)
        self.assertEqual(ParcelaFinanceira.objects.count(), 0)

    def test_numeros_de_parcela_duplicados_devem_falhar_atomicamente(self):
        from financeiro.services import criar_titulo_financeiro
        dados = self._kwargs()
        dados["parcelas"][1]["numero"] = 1
        with self.assertRaises(ValidationError):
            criar_titulo_financeiro(**dados)
        self.assertEqual(TituloFinanceiro.objects.count(), 0)
        self.assertEqual(ParcelaFinanceira.objects.count(), 0)