from datetime import date
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.test import TestCase
from empresas.models import Matriz
from financeiro.models import TituloFinanceiro
from financeiro.services import criar_titulo_financeiro

class IdempotenciaEstruturaParcelasTests(TestCase):
    def setUp(self):
        self.matriz=Matriz.objects.create(nome="Matriz Parcelas Idempotencia")
        self.base=dict(
            matriz=self.matriz, loja=None, natureza=TituloFinanceiro.Natureza.RECEBER,
            origem_tipo="MANUAL", origem_id="idem-parcelas-001",
            chave_idempotencia="idem-parcelas-chave-001", descricao="Contrato parcelas",
            data_emissao=date(2026,9,14),
        )
        self.parcelas=[
            {"numero":1,"vencimento":date(2026,10,14),"valor":Decimal("60.00")},
            {"numero":2,"vencimento":date(2026,11,14),"valor":Decimal("40.00")},
        ]
        self.titulo=criar_titulo_financeiro(**self.base, parcelas=self.parcelas)

    def test_mesma_chave_mesmo_total_vencimento_diferente_deve_rejeitar(self):
        alteradas=[
            {"numero":1,"vencimento":date(2026,10,15),"valor":Decimal("60.00")},
            {"numero":2,"vencimento":date(2026,11,14),"valor":Decimal("40.00")},
        ]
        with self.assertRaises(ValidationError):
            criar_titulo_financeiro(**self.base, parcelas=alteradas)

    def test_mesma_chave_mesmo_total_rateio_diferente_deve_rejeitar(self):
        alteradas=[
            {"numero":1,"vencimento":date(2026,10,14),"valor":Decimal("50.00")},
            {"numero":2,"vencimento":date(2026,11,14),"valor":Decimal("50.00")},
        ]
        with self.assertRaises(ValidationError):
            criar_titulo_financeiro(**self.base, parcelas=alteradas)

    def test_mesma_chave_numeracao_diferente_deve_rejeitar(self):
        alteradas=[
            {"numero":2,"vencimento":date(2026,10,14),"valor":Decimal("60.00")},
            {"numero":3,"vencimento":date(2026,11,14),"valor":Decimal("40.00")},
        ]
        with self.assertRaises(ValidationError):
            criar_titulo_financeiro(**self.base, parcelas=alteradas)

    def test_repeticao_exata_da_estrutura_deve_retornar_mesmo_titulo(self):
        repetido=criar_titulo_financeiro(**self.base, parcelas=list(reversed(self.parcelas)))
        self.assertEqual(repetido.pk,self.titulo.pk)
        self.assertEqual(TituloFinanceiro.objects.count(),1)
        self.assertEqual(self.titulo.parcelas.count(),2)