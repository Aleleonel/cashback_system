"""F32P4H88Q4E40AH: contratos transacionais de repasse, banco Django temporario."""
from datetime import date
from decimal import Decimal
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError, PermissionDenied
from django.test import TestCase
from empresas.models import Matriz, Loja
from financeiro.models import PlanoConta, ContaFinanceira, TituloFinanceiro, BaixaFinanceira
from financeiro.services import criar_titulo_financeiro
from financeiro.conciliacao_adquirente import registrar_repasse_adquirente, estornar_repasse_adquirente
from pdv.models import Venda, PagamentoVenda, FormaPagamento
from pdv.choices import TipoFormaPagamento


class RepasseTransacionalAHTests(TestCase):
    def setUp(self):
        self.hoje = date(2026, 11, 12)
        self.matriz = Matriz.objects.create(nome='Matriz AH')
        self.loja = Loja.objects.create(matriz=self.matriz, nome='Loja AH')
        self.usuario = get_user_model().objects.create_superuser(username='ah_admin', password='teste', email='ah@example.invalid')
        self.forma = FormaPagamento.objects.create(matriz=self.matriz, nome='Cartao AH', codigo='AH-CC', tipo=TipoFormaPagamento.CARTAO_CREDITO, movimenta_caixa=False)
        self.conta = ContaFinanceira.objects.create(matriz=self.matriz, loja=self.loja, nome='Banco AH', tipo=ContaFinanceira.Tipo.CONTA_CORRENTE)
        self.plano = PlanoConta.objects.create(matriz=self.matriz, codigo='AH-TAXA', nome='Taxas AH', tipo=PlanoConta.Tipo.ANALITICA, natureza=PlanoConta.Natureza.DESPESA, classificacao_dre=PlanoConta.ClassificacaoDRE.RESULTADO_FINANCEIRO)
        venda = Venda.objects.create(matriz=self.matriz, loja=self.loja, operador=self.usuario, total=Decimal('100.00'))
        pagamento = PagamentoVenda.objects.create(venda=venda, forma_pagamento=self.forma, valor=Decimal('100.00'))
        self.titulo = criar_titulo_financeiro(matriz=self.matriz, loja=self.loja, natureza=TituloFinanceiro.Natureza.RECEBER, origem_tipo=TituloFinanceiro.OrigemTipo.VENDA_PAGAMENTO, origem_id=str(pagamento.uuid), chave_idempotencia=f'venda-pagamento:{pagamento.uuid}', descricao='Recebivel AH', data_emissao=self.hoje, parcelas=[{'numero': 1, 'vencimento': self.hoje, 'valor': Decimal('100.00')}])
        self.parcela = self.titulo.parcelas.get()

    def registrar(self, **changes):
        params = dict(parcela=self.parcela, bruto='100.00', taxa='3.00', data=self.hoje, chave_idempotencia='ah-001', forma_pagamento=self.forma, conta_financeira=self.conta, plano_taxas=self.plano, usuario=self.usuario)
        params.update(changes)
        return registrar_repasse_adquirente(**params)

    def test_registro_bruto_taxa_liquido_e_sem_caixa_fisico(self):
        r = self.registrar()
        self.assertEqual(r['liquido'], Decimal('97.00'))
        self.assertEqual(r['baixa'].valor, Decimal('100.00'))
        self.assertIsNone(r['baixa'].movimentacao_caixa_id)
        self.assertEqual(r['titulo_taxa'].valor_original, Decimal('3.00'))
        self.assertEqual(BaixaFinanceira.objects.filter(tipo=BaixaFinanceira.Tipo.BAIXA).count(), 2)
        self.parcela.refresh_from_db()
        self.assertEqual(self.parcela.status, self.parcela.Status.LIQUIDADO)

    def test_repeticao_nao_duplica_titulo_nem_baixas(self):
        primeiro = self.registrar()
        segundo = self.registrar()
        self.assertEqual(primeiro['baixa'].pk, segundo['baixa'].pk)
        self.assertEqual(primeiro['titulo_taxa'].pk, segundo['titulo_taxa'].pk)
        self.assertEqual(TituloFinanceiro.objects.count(), 2)
        self.assertEqual(BaixaFinanceira.objects.count(), 2)

    def test_conta_de_outra_loja_rejeitada_sem_gravacao(self):
        outra = Loja.objects.create(matriz=self.matriz, nome='Outra loja AH')
        conta = ContaFinanceira.objects.create(matriz=self.matriz, loja=outra, nome='Outra conta AH', tipo=ContaFinanceira.Tipo.CONTA_CORRENTE)
        with self.assertRaises(ValidationError):
            self.registrar(conta_financeira=conta)
        self.assertEqual(BaixaFinanceira.objects.count(), 0)
        self.assertEqual(TituloFinanceiro.objects.count(), 1)

    def test_falha_no_pagamento_taxa_faz_rollback_total(self):
        from financeiro import conciliacao_adquirente as modulo
        original = modulo.registrar_baixa_financeira_com_caixa
        def falhar_na_taxa(*args, **kwargs):
            if kwargs['chave_idempotencia'].endswith(':pagamento-taxa'):
                raise RuntimeError('falha simulada depois de criar a despesa')
            return original(*args, **kwargs)
        with patch.object(modulo, 'registrar_baixa_financeira_com_caixa', side_effect=falhar_na_taxa):
            with self.assertRaises(RuntimeError):
                self.registrar()
        self.assertEqual(TituloFinanceiro.objects.count(), 1)
        self.assertEqual(BaixaFinanceira.objects.count(), 0)

    def test_estorno_conjunto_e_repeticao_bloqueada(self):
        r = self.registrar()
        estorno = estornar_repasse_adquirente(baixa=r['baixa'], data=self.hoje, chave_idempotencia='ah-estorno', motivo='Reversao integral de teste', usuario=self.usuario)
        self.assertEqual(estorno.tipo, BaixaFinanceira.Tipo.ESTORNO)
        self.assertEqual(BaixaFinanceira.objects.filter(tipo=BaixaFinanceira.Tipo.ESTORNO).count(), 2)
        self.parcela.refresh_from_db()
        self.assertEqual(self.parcela.status, self.parcela.Status.ABERTO)
        with self.assertRaises(ValidationError):
            self.registrar()

    def test_estorno_sem_autorizacao_rejeitado(self):
        r = self.registrar()
        sem_permissao = get_user_model().objects.create_user(username='ah_sem_permissao', password='teste', matriz=self.matriz)
        with self.assertRaises(PermissionDenied):
            estornar_repasse_adquirente(baixa=r['baixa'], data=self.hoje, chave_idempotencia='ah-nao', motivo='Tentativa sem permissao', usuario=sem_permissao)
        self.assertFalse(BaixaFinanceira.objects.filter(tipo=BaixaFinanceira.Tipo.ESTORNO).exists())
