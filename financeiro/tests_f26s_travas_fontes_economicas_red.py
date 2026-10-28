from datetime import date
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

from accounts.models import Usuario
from empresas.models import Matriz, Loja
from financeiro.models import PlanoConta, TituloFinanceiro, FechamentoGerencial
from financeiro.services import criar_lancamento_manual
from configuracoes.models import FechamentoComissao, ComissaoVendedor
from configuracoes.services_comissoes import fechar_comissoes_competencia


class F26STravasFontesEconomicasRestantesTests(TestCase):
    def setUp(self):
        self.matriz = Matriz.objects.create(nome="F26S MATRIZ")
        self.loja = Loja.objects.create(matriz=self.matriz, nome="F26S LOJA")
        self.user = Usuario.objects.create_user(username="f26s", email="f26s@example.com", password="x")
        self.plano = PlanoConta.objects.create(
            matriz=self.matriz, codigo="F26S.1", nome="Despesa F26S",
            tipo=PlanoConta.Tipo.ANALITICA, natureza=PlanoConta.Natureza.DESPESA,
            classificacao_dre=PlanoConta.ClassificacaoDRE.DESPESA_OPERACIONAL,
            aceita_lancamento=True, ativo=True,
        )

    def _titulo(self, dia=date(2026, 10, 10)):
        return criar_lancamento_manual(
            matriz=self.matriz, loja=self.loja,
            natureza=TituloFinanceiro.Natureza.PAGAR,
            chave_idempotencia=f"F26S:{dia.isoformat()}",
            descricao="Lancamento economico F26S",
            data_emissao=dia,
            data_competencia=dia,
            valor_bruto=Decimal("100.00"),
            parcelas=[{"numero": 1, "vencimento": dia, "valor": Decimal("100.00")}],
            plano_conta=self.plano,
            usuario=self.user,
        )

    def _fechar_gerencial(self):
        return FechamentoGerencial.objects.create(
            matriz=self.matriz, competencia_ano=2026, competencia_mes=10,
            status=FechamentoGerencial.Status.FECHADO,
            fechado_por=self.user,
        )

    def test_plano_usado_em_competencia_fechada_nao_pode_mudar_classificacao_dre(self):
        self._titulo()
        self._fechar_gerencial()
        self.plano.classificacao_dre = PlanoConta.ClassificacaoDRE.RESULTADO_FINANCEIRO
        with self.assertRaises(ValidationError):
            self.plano.save()

    def test_plano_usado_em_competencia_fechada_nao_pode_mudar_natureza(self):
        self._titulo()
        self._fechar_gerencial()
        self.plano.natureza = PlanoConta.Natureza.ATIVO
        with self.assertRaises(ValidationError):
            self.plano.save()

    def test_plano_sem_uso_em_competencia_fechada_pode_mudar_classificacao(self):
        self.plano.classificacao_dre = PlanoConta.ClassificacaoDRE.RESULTADO_FINANCEIRO
        self.plano.save()
        self.plano.refresh_from_db()
        self.assertEqual(self.plano.classificacao_dre, PlanoConta.ClassificacaoDRE.RESULTADO_FINANCEIRO)

    def test_plano_usado_apenas_em_competencia_aberta_pode_mudar_classificacao(self):
        self._titulo()
        self.plano.classificacao_dre = PlanoConta.ClassificacaoDRE.RESULTADO_FINANCEIRO
        self.plano.save()
        self.plano.refresh_from_db()
        self.assertEqual(self.plano.classificacao_dre, PlanoConta.ClassificacaoDRE.RESULTADO_FINANCEIRO)

    def test_fechamento_comissao_persistido_e_imutavel(self):
        f = FechamentoComissao.objects.create(
            matriz=self.matriz, loja=self.loja, competencia_ano=2026, competencia_mes=9,
            total_vendas_loja=Decimal("0.00"), percentual_aplicado=Decimal("0.0000"),
            exigir_minimo_individual=False, minimo_individual=Decimal("0.00"),
        )
        f.total_vendas_loja = Decimal("1.00")
        with self.assertRaises(ValidationError):
            f.save()
        with self.assertRaises(ValidationError):
            f.delete()

    def test_comissao_vendedor_persistida_e_imutavel(self):
        f = FechamentoComissao.objects.create(
            matriz=self.matriz, loja=self.loja, competencia_ano=2026, competencia_mes=9,
            total_vendas_loja=Decimal("0.00"), percentual_aplicado=Decimal("0.0000"),
            exigir_minimo_individual=False, minimo_individual=Decimal("0.00"),
        )
        c = ComissaoVendedor.objects.create(
            fechamento=f, vendedor=self.user, vendedor_uuid_original=self.user.uuid,
            vendedor_nome_original="F26S", total_vendas_vendedor=Decimal("0.00"),
            elegivel=True, valor_comissao=Decimal("0.00"),
        )
        c.valor_comissao = Decimal("1.00")
        with self.assertRaises(ValidationError):
            c.save()
        with self.assertRaises(ValidationError):
            c.delete()

    def test_fechamento_comissao_novo_nao_pode_nascer_em_competencia_gerencial_fechada(self):
        self._fechar_gerencial()
        with self.assertRaises(ValidationError):
            fechar_comissoes_competencia(loja=self.loja, ano=2026, mes=10)