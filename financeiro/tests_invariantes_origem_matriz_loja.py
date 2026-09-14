from datetime import date
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.test import TestCase
from empresas.models import Matriz, Loja
from financeiro.models import TituloFinanceiro
from financeiro.services import criar_titulo_financeiro

class InvariantesOrigemMatrizLojaTests(TestCase):
    def setUp(self):
        self.matriz_a=Matriz.objects.create(nome="Matriz A Financeiro")
        self.matriz_b=Matriz.objects.create(nome="Matriz B Financeiro")
        self.loja_b=Loja.objects.create(matriz=self.matriz_b,nome="Loja B Financeiro")
        self.base=dict(
            matriz=self.matriz_a, loja=None, natureza=TituloFinanceiro.Natureza.RECEBER,
            origem_tipo="MANUAL", origem_id="origem-estavel-001",
            chave_idempotencia="chave-origem-001", descricao="Contrato origem",
            data_emissao=date(2026,9,14),
            parcelas=[{"numero":1,"vencimento":date(2026,10,14),"valor":Decimal("100.00")}],
        )

    def test_loja_de_outra_matriz_deve_ser_rejeitada(self):
        dados=dict(self.base)
        dados["loja"]=self.loja_b
        with self.assertRaises(ValidationError):
            criar_titulo_financeiro(**dados)
        self.assertEqual(TituloFinanceiro.objects.count(),0)

    def test_mesma_origem_estavel_com_chave_idempotencia_diferente_deve_rejeitar(self):
        primeiro=criar_titulo_financeiro(**self.base)
        dados=dict(self.base)
        dados["chave_idempotencia"]="chave-origem-002"
        with self.assertRaises(ValidationError):
            criar_titulo_financeiro(**dados)
        self.assertEqual(TituloFinanceiro.objects.count(),1)
        self.assertTrue(TituloFinanceiro.objects.filter(pk=primeiro.pk).exists())

    def test_mesma_origem_em_matriz_diferente_deve_ser_permitida(self):
        criar_titulo_financeiro(**self.base)
        dados=dict(self.base)
        dados["matriz"]=self.matriz_b
        dados["chave_idempotencia"]="chave-matriz-b-001"
        segundo=criar_titulo_financeiro(**dados)
        self.assertEqual(TituloFinanceiro.objects.count(),2)
        self.assertEqual(segundo.matriz_id,self.matriz_b.id)