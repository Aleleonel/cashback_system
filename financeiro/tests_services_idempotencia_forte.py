from datetime import date
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

from empresas.models import Matriz
from financeiro.models import TituloFinanceiro
from financeiro.services import criar_titulo_financeiro


class IdempotenciaForteCriacaoTituloTests(TestCase):
    def setUp(self):
        self.matriz = Matriz.objects.create(nome="Matriz Idempotencia Forte")

    def _dados(self):
        return {
            "matriz": self.matriz,
            "loja": None,
            "natureza": TituloFinanceiro.Natureza.PAGAR,
            "origem_tipo": "MANUAL",
            "origem_id": "manual-forte-001",
            "chave_idempotencia": "idem-forte-001",
            "descricao": "Titulo idempotencia forte",
            "data_emissao": date(2026, 9, 14),
            "parcelas": [
                {"numero": 1, "vencimento": date(2026, 10, 14), "valor": Decimal("100.00")},
            ],
        }

    def test_repeticao_identica_deve_retornar_mesmo_titulo(self):
        dados = self._dados()
        primeiro = criar_titulo_financeiro(**dados)
        segundo = criar_titulo_financeiro(**dados)
        self.assertEqual(primeiro.pk, segundo.pk)

    def test_mesma_chave_com_valor_diferente_deve_rejeitar(self):
        primeiro = self._dados()
        criar_titulo_financeiro(**primeiro)
        conflito = self._dados()
        conflito["parcelas"][0]["valor"] = Decimal("101.00")
        with self.assertRaises(ValidationError):
            criar_titulo_financeiro(**conflito)

    def test_mesma_chave_com_origem_diferente_deve_rejeitar(self):
        primeiro = self._dados()
        criar_titulo_financeiro(**primeiro)
        conflito = self._dados()
        conflito["origem_id"] = "manual-forte-OUTRA"
        with self.assertRaises(ValidationError):
            criar_titulo_financeiro(**conflito)

    def test_mesma_chave_em_matriz_diferente_pode_existir(self):
        outra = Matriz.objects.create(nome="Outra Matriz Idempotencia")
        primeiro = criar_titulo_financeiro(**self._dados())
        dados_outra = self._dados()
        dados_outra["matriz"] = outra
        segundo = criar_titulo_financeiro(**dados_outra)
        self.assertNotEqual(primeiro.pk, segundo.pk)
        self.assertEqual(TituloFinanceiro.objects.count(), 2)