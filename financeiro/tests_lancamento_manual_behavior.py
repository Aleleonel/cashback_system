from datetime import date
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.test import TestCase

from empresas.models import Matriz, Loja
from financeiro.models import CentroCusto, PlanoConta, TituloFinanceiro
from financeiro.services import criar_lancamento_manual


class LancamentoManualBehaviorTests(TestCase):
    def setUp(self):
        self.matriz = Matriz.objects.create(nome="Matriz R6B")
        self.outra_matriz = Matriz.objects.create(nome="Outra Matriz R6B")
        self.loja = Loja.objects.create(matriz=self.matriz, nome="Loja R6B")
        self.loja_outra = Loja.objects.create(matriz=self.outra_matriz, nome="Loja Outra R6B")
        self.plano = PlanoConta.objects.create(
            matriz=self.matriz, codigo="3.1.01", nome="Limpeza",
            tipo=PlanoConta.Tipo.ANALITICA, natureza=PlanoConta.Natureza.DESPESA,
            aceita_lancamento=True, ativo=True,
        )
        self.centro = CentroCusto.objects.create(
            matriz=self.matriz, codigo="ADM", nome="Administrativo", ativo=True
        )

    def payload(self, **extra):
        dados = dict(
            matriz=self.matriz,
            loja=self.loja,
            natureza=TituloFinanceiro.Natureza.PAGAR,
            chave_idempotencia="manual-r6b-001",
            descricao="Servico de limpeza",
            data_emissao=date(2026, 9, 14),
            data_competencia=date(2026, 9, 1),
            valor_bruto=Decimal("100.00"),
            valor_desconto=Decimal("0.00"),
            valor_juros=Decimal("0.00"),
            observacao="Lancamento manual R6 atualizado para contrato R8",
            parcelas=[
                {"numero": 1, "vencimento": date(2026, 9, 20), "valor": "60.00"},
                {"numero": 2, "vencimento": date(2026, 10, 20), "valor": "40.00"},
            ],
            plano_conta=self.plano,
            centro_custo=self.centro,
            entidade_nome="Prestador Limpeza",
            documento_referencia="DOC-001",
        )
        dados.update(extra)
        return dados

    def test_cria_manual_com_classificacao_e_parcelas(self):
        titulo = criar_lancamento_manual(**self.payload())
        self.assertEqual(titulo.origem_tipo, TituloFinanceiro.OrigemTipo.MANUAL)
        self.assertEqual(titulo.valor_original, 100)
        self.assertEqual(titulo.plano_conta, self.plano)
        self.assertEqual(titulo.centro_custo, self.centro)
        self.assertEqual(titulo.entidade_nome, "Prestador Limpeza")
        self.assertEqual(titulo.documento_referencia, "DOC-001")
        self.assertEqual(titulo.parcelas.count(), 2)

    def test_rejeita_plano_sintetico(self):
        plano = PlanoConta.objects.create(
            matriz=self.matriz, codigo="3.1", nome="Despesas",
            tipo=PlanoConta.Tipo.SINTETICA, natureza=PlanoConta.Natureza.DESPESA,
            aceita_lancamento=False, ativo=True,
        )
        with self.assertRaises(ValidationError):
            criar_lancamento_manual(**self.payload(plano_conta=plano, chave_idempotencia="manual-r6b-002"))

    def test_rejeita_plano_inativo(self):
        self.plano.ativo = False
        self.plano.save(update_fields=["ativo"])
        with self.assertRaises(ValidationError):
            criar_lancamento_manual(**self.payload(chave_idempotencia="manual-r6b-003"))

    def test_rejeita_plano_de_outra_matriz(self):
        plano = PlanoConta.objects.create(
            matriz=self.outra_matriz, codigo="3.1.01", nome="Outra",
            tipo=PlanoConta.Tipo.ANALITICA, natureza=PlanoConta.Natureza.DESPESA,
            aceita_lancamento=True, ativo=True,
        )
        with self.assertRaises(ValidationError):
            criar_lancamento_manual(**self.payload(plano_conta=plano, chave_idempotencia="manual-r6b-004"))

    def test_rejeita_loja_de_outra_matriz(self):
        with self.assertRaises(ValidationError):
            criar_lancamento_manual(**self.payload(loja=self.loja_outra, chave_idempotencia="manual-r6b-005"))

    def test_rejeita_centro_custo_de_outra_matriz(self):
        centro = CentroCusto.objects.create(
            matriz=self.outra_matriz, codigo="ADM", nome="Outro ADM", ativo=True
        )
        with self.assertRaises(ValidationError):
            criar_lancamento_manual(**self.payload(centro_custo=centro, chave_idempotencia="manual-r6b-006"))

    def test_idempotencia_retorna_mesmo_titulo(self):
        primeiro = criar_lancamento_manual(**self.payload(chave_idempotencia="manual-r6b-007"))
        segundo = criar_lancamento_manual(**self.payload(chave_idempotencia="manual-r6b-007"))
        self.assertEqual(primeiro.pk, segundo.pk)
        self.assertEqual(TituloFinanceiro.objects.filter(chave_idempotencia="manual-r6b-007").count(), 1)