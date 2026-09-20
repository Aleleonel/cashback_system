from datetime import date, timedelta
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.test import TestCase
from empresas.models import Matriz
from financeiro.models import CentroCusto, PlanoConta, TituloFinanceiro
from financeiro.services import criar_lancamento_manual

class HardeningManualBehaviorTests(TestCase):
    def setUp(self):
        self.matriz=Matriz.objects.create(nome="Matriz R8D", cnpj="12345678000195")
        self.plano=PlanoConta.objects.create(
            matriz=self.matriz,codigo="3.1.01",nome="Despesa teste",
            tipo=PlanoConta.Tipo.ANALITICA,natureza=PlanoConta.Natureza.DESPESA,
            aceita_lancamento=True,ativo=True,
        )
        self.cc=CentroCusto.objects.create(matriz=self.matriz,codigo="ADM",nome="Administrativo",ativo=True)
        self.base=dict(
            matriz=self.matriz,loja=None,natureza=TituloFinanceiro.Natureza.PAGAR,
            chave_idempotencia="R8D-MANUAL-001",descricao="Servico contabil",
            data_emissao=date(2026,9,14),
            parcelas=[
                {"numero":1,"vencimento":date(2026,10,10),"valor":Decimal("450.00")},
                {"numero":2,"vencimento":date(2026,11,10),"valor":Decimal("450.00")},
            ],
            plano_conta=self.plano,centro_custo=self.cc,entidade_nome="Fornecedor XPTO",
            documento_referencia="NF-123",data_competencia=date(2026,9,1),
            valor_bruto=Decimal("1000.00"),valor_desconto=Decimal("150.00"),
            valor_juros=Decimal("50.00"),observacao="Contrato mensal",
        )

    def test_calculo_persistencia_e_parcelas(self):
        titulo=criar_lancamento_manual(**self.base)
        titulo.refresh_from_db()
        self.assertEqual(titulo.valor_original,Decimal("900.00"))
        self.assertEqual(titulo.valor_bruto,Decimal("1000.00"))
        self.assertEqual(titulo.valor_desconto,Decimal("150.00"))
        self.assertEqual(titulo.valor_juros,Decimal("50.00"))
        self.assertEqual(titulo.data_competencia,date(2026,9,1))
        self.assertEqual(titulo.observacao,"Contrato mensal")
        self.assertEqual(titulo.parcelas.count(),2)
        self.assertEqual(sum((p.valor_original for p in titulo.parcelas.all()), Decimal("0.00")), Decimal("900.00"))

    def test_mesma_chave_mesmo_payload_retorna_mesmo_titulo_sem_duplicar(self):
        primeiro=criar_lancamento_manual(**self.base)
        segundo=criar_lancamento_manual(**self.base)
        self.assertEqual(primeiro.pk,segundo.pk)
        self.assertEqual(TituloFinanceiro.objects.filter(matriz=self.matriz,chave_idempotencia="R8D-MANUAL-001").count(),1)
        self.assertEqual(primeiro.parcelas.count(),2)

    def test_mesma_chave_classificacao_diferente_rejeita_sem_mutar(self):
        original=criar_lancamento_manual(**self.base)
        outro=PlanoConta.objects.create(
            matriz=self.matriz,codigo="3.1.02",nome="Outra despesa",
            tipo=PlanoConta.Tipo.ANALITICA,natureza=PlanoConta.Natureza.DESPESA,
            aceita_lancamento=True,ativo=True,
        )
        alterado=dict(self.base);alterado["plano_conta"]=outro
        with self.assertRaises(ValidationError):
            criar_lancamento_manual(**alterado)
        original.refresh_from_db()
        self.assertEqual(original.plano_conta_id,self.plano.pk)
        self.assertEqual(original.entidade_nome,"Fornecedor XPTO")

    def test_mesma_chave_payload_financeiro_diferente_rejeita_sem_mutar(self):
        original=criar_lancamento_manual(**self.base)
        alterado=dict(self.base);alterado["observacao"]="Tentativa de alterar"
        with self.assertRaises(ValidationError):
            criar_lancamento_manual(**alterado)
        original.refresh_from_db()
        self.assertEqual(original.observacao,"Contrato mensal")
        self.assertEqual(original.valor_original,Decimal("900.00"))

    def test_soma_parcelas_diferente_do_valor_final_rejeita_sem_criar(self):
        alterado=dict(self.base)
        alterado["parcelas"]=[{"numero":1,"vencimento":date(2026,10,10),"valor":Decimal("899.99")}]
        with self.assertRaises(ValidationError):
            criar_lancamento_manual(**alterado)
        self.assertFalse(TituloFinanceiro.objects.filter(chave_idempotencia="R8D-MANUAL-001").exists())

    def test_competencia_e_bruto_obrigatorios_no_manual(self):
        for campo in ("data_competencia","valor_bruto"):
            alterado=dict(self.base);alterado[campo]=None
            with self.subTest(campo=campo):
                with self.assertRaises(ValidationError):
                    criar_lancamento_manual(**alterado)
        self.assertFalse(TituloFinanceiro.objects.filter(chave_idempotencia="R8D-MANUAL-001").exists())

    def test_desconto_ou_juros_negativo_rejeita(self):
        for campo in ("valor_desconto","valor_juros"):
            alterado=dict(self.base);alterado[campo]=Decimal("-0.01")
            with self.subTest(campo=campo):
                with self.assertRaises(ValidationError):
                    criar_lancamento_manual(**alterado)
        self.assertFalse(TituloFinanceiro.objects.filter(chave_idempotencia="R8D-MANUAL-001").exists())