from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from auditoria.models import RegistroAuditoria
from empresas.models import Matriz, Loja
from financeiro.models import CentroCusto, FechamentoGerencial, PlanoConta, TituloFinanceiro
from financeiro.services import criar_lancamento_manual
from accounts.permissions import PERMISSAO_FINANCEIRO_EDITAR_LANCAMENTO
from accounts.models import PermissaoUsuario


class F26Z3EdicaoManualSemBaixaRED(TestCase):
    def setUp(self):
        self.matriz = Matriz.objects.create(nome="F26Z3 Matriz")
        self.loja = Loja.objects.create(matriz=self.matriz, nome="F26Z3 Loja")
        self.user = get_user_model().objects.create_user(username="f26z3", password="x")
        PermissaoUsuario.objects.create(usuario=self.user, permissao=PERMISSAO_FINANCEIRO_EDITAR_LANCAMENTO)
        self.plano = PlanoConta.objects.create(
            matriz=self.matriz, codigo="9.01", nome="Despesa F26Z3",
            tipo=PlanoConta.Tipo.ANALITICA, natureza=PlanoConta.Natureza.DESPESA,
            classificacao_dre=PlanoConta.ClassificacaoDRE.DESPESA_OPERACIONAL,
            aceita_lancamento=True, ativo=True,
        )
        self.cc = CentroCusto.objects.create(
            matriz=self.matriz, codigo="Z3", nome="Centro F26Z3", ativo=True
        )
        self.titulo = criar_lancamento_manual(
            matriz=self.matriz, loja=self.loja, natureza=TituloFinanceiro.Natureza.PAGAR,
            chave_idempotencia="f26z3-original", descricao="Original",
            data_emissao=date(2026, 11, 1),
            parcelas=[{"numero": 1, "vencimento": date(2026, 11, 20), "valor": Decimal("100.00")}],
            plano_conta=self.plano, centro_custo=self.cc, entidade_nome="Fornecedor A",
            documento_referencia="DOC-1", data_competencia=date(2026, 11, 1),
            valor_bruto=Decimal("100.00"), valor_desconto=Decimal("0.00"),
            valor_juros=Decimal("0.00"), observacao="antes", usuario=self.user,
        )
        self.user.matriz = self.matriz
        self.user.save(update_fields=['matriz'])
        self.user.lojas.add(self.loja)

    def atualizar(self, **overrides):
        from financeiro.services import atualizar_lancamento_manual
        dados = dict(
            titulo=self.titulo, loja=self.loja, natureza=TituloFinanceiro.Natureza.PAGAR,
            descricao="Corrigido", data_emissao=date(2026, 11, 2),
            parcelas=[{"numero": 1, "vencimento": date(2026, 11, 25), "valor": Decimal("120.00")}],
            plano_conta=self.plano, centro_custo=self.cc, entidade_nome="Fornecedor B",
            documento_referencia="DOC-2", data_competencia=date(2026, 11, 2),
            valor_bruto=Decimal("120.00"), valor_desconto=Decimal("0.00"),
            valor_juros=Decimal("0.00"), observacao="depois", usuario=self.user,
        )
        dados.update(overrides)
        return atualizar_lancamento_manual(**dados)

    def fechar(self, ano, mes):
        FechamentoGerencial.objects.create(
            matriz=self.matriz, competencia_ano=ano, competencia_mes=mes,
            status=FechamentoGerencial.Status.FECHADO, fechado_por=self.user
        )

    def test_01_manual_aberto_sem_baixa_pode_ser_corrigido(self):
        atualizado = self.atualizar()
        atualizado.refresh_from_db()
        self.assertEqual(atualizado.valor_bruto, Decimal("120.00"))
        self.assertEqual(atualizado.descricao, "Corrigido")
        self.assertEqual(atualizado.parcelas.count(), 1)
        self.assertEqual(atualizado.parcelas.get().valor_original, Decimal("120.00"))

    def test_02_origem_tecnica_permanece_imutavel(self):
        origem_tipo, origem_id, chave, uuid = self.titulo.origem_tipo, self.titulo.origem_id, self.titulo.chave_idempotencia, self.titulo.uuid
        atualizado = self.atualizar()
        atualizado.refresh_from_db()
        self.assertEqual((atualizado.origem_tipo, atualizado.origem_id, atualizado.chave_idempotencia, atualizado.uuid),
                         (origem_tipo, origem_id, chave, uuid))

    def test_03_rejeita_titulo_automatico(self):
        self.titulo.origem_tipo = TituloFinanceiro.OrigemTipo.COMPRA_RECEBIMENTO
        self.titulo.save(update_fields=["origem_tipo"])
        with self.assertRaises(ValidationError):
            self.atualizar()

    def test_04_rejeita_titulo_cancelado(self):
        self.titulo.status = TituloFinanceiro.Status.CANCELADO
        self.titulo.save(update_fields=["status"])
        with self.assertRaises(ValidationError):
            self.atualizar()

    def test_05_rejeita_titulo_com_baixa_ou_nao_aberto(self):
        self.titulo.status = TituloFinanceiro.Status.LIQUIDADO
        self.titulo.save(update_fields=["status"])
        with self.assertRaises(ValidationError):
            self.atualizar()

    def test_06_competencia_origem_fechada_bloqueia(self):
        self.fechar(2026, 11)
        with self.assertRaises(ValidationError):
            self.atualizar(data_competencia=date(2026, 12, 2))

    def test_07_competencia_destino_fechada_bloqueia(self):
        self.fechar(2026, 12)
        with self.assertRaises(ValidationError):
            self.atualizar(data_competencia=date(2026, 12, 2))

    def test_08_edicao_gera_auditoria(self):
        self.atualizar()
        self.assertTrue(
            RegistroAuditoria.objects.filter(
                matriz=self.matriz, acao=RegistroAuditoria.ACAO_EDITAR,
                recurso="financeiro.titulo", recurso_id=str(self.titulo.uuid)
            ).exists()
        )