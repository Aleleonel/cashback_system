from datetime import date
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

from accounts.models import PermissaoUsuario, Usuario
from accounts.permissions import PERMISSAO_FINANCEIRO_CANCELAR_LANCAMENTO
from empresas.models import Matriz
from financeiro.models import FechamentoGerencial, PlanoConta, TituloFinanceiro
from financeiro.services import (
    cancelar_titulo_financeiro,
    criar_lancamento_manual,
    validar_fechamento_gerencial,
)


class F26PTravasSemanticaRedTests(TestCase):
    def setUp(self):
        self.matriz = Matriz.objects.create(nome="F26P Matriz")
        self.usuario = Usuario.objects.create_user(
            username="f26p", email="f26p@example.com", password="x",
            matriz=self.matriz, perfil=Usuario.PERFIL_MASTER,
        )

        PermissaoUsuario.objects.create(usuario=self.usuario, permissao=PERMISSAO_FINANCEIRO_CANCELAR_LANCAMENTO)

    def plano(self, natureza, classificacao=None, codigo="P"):
        return PlanoConta.objects.create(
            matriz=self.matriz,
            codigo=codigo,
            nome=codigo,
            tipo=PlanoConta.Tipo.ANALITICA,
            natureza=natureza,
            aceita_lancamento=True,
            classificacao_dre=classificacao,
        )

    def criar_manual(self, plano, chave="f26p-manual"):
        return criar_lancamento_manual(
            matriz=self.matriz,
            loja=None,
            natureza=TituloFinanceiro.Natureza.PAGAR,
            chave_idempotencia=chave,
            descricao="F26P",
            data_emissao=date(2026, 9, 10),
            parcelas=[
                {"numero": 1, "vencimento": date(2026, 9, 20), "valor": Decimal("10.00")}
            ],
            plano_conta=plano,
            centro_custo=None,
            entidade_nome="F26P",
            documento_referencia="F26P",
            data_competencia=date(2026, 9, 10),
            valor_bruto=Decimal("10.00"),
            valor_desconto=Decimal("0.00"),
            valor_juros=Decimal("0.00"),
            observacao="",
            usuario=self.usuario,
        )

    def item_classificacao(self):
        resultado = validar_fechamento_gerencial(
            matriz=self.matriz, competencia_ano=2026, competencia_mes=9
        )
        return next(
            item
            for item in resultado["itens"]
            if item["codigo"] == "LANCAMENTOS_ECONOMICOS_CLASSIFICADOS_DRE"
        )

    def fechar(self):
        return FechamentoGerencial.objects.create(
            matriz=self.matriz,
            competencia_ano=2026,
            competencia_mes=9,
            status=FechamentoGerencial.Status.FECHADO,
            fechado_por=self.usuario,
        )

    def test_despesa_sem_classificacao_bloqueia(self):
        self.criar_manual(self.plano(PlanoConta.Natureza.DESPESA, None, "D"))
        self.assertEqual(self.item_classificacao()["status"], "PENDENTE")

    def test_receita_sem_classificacao_bloqueia(self):
        self.criar_manual(self.plano(PlanoConta.Natureza.RECEITA, None, "R"))
        self.assertEqual(self.item_classificacao()["status"], "PENDENTE")

    def test_ativo_sem_classificacao_nao_bloqueia(self):
        self.criar_manual(self.plano(PlanoConta.Natureza.ATIVO, None, "A"))
        self.assertEqual(self.item_classificacao()["status"], "OK")

    def test_passivo_sem_classificacao_nao_bloqueia(self):
        self.criar_manual(self.plano(PlanoConta.Natureza.PASSIVO, None, "P"))
        self.assertEqual(self.item_classificacao()["status"], "OK")

    def test_outro_sem_classificacao_nao_bloqueia(self):
        self.criar_manual(self.plano(PlanoConta.Natureza.OUTRO, None, "O"))
        self.assertEqual(self.item_classificacao()["status"], "OK")

    def test_criacao_manual_em_competencia_fechada_bloqueia(self):
        plano = self.plano(
            PlanoConta.Natureza.DESPESA,
            PlanoConta.ClassificacaoDRE.DESPESA_OPERACIONAL,
            "CF",
        )
        self.fechar()
        with self.assertRaises(ValidationError):
            self.criar_manual(plano, "f26p-fechada-criar")

    def test_cancelamento_manual_em_competencia_fechada_bloqueia(self):
        plano = self.plano(
            PlanoConta.Natureza.DESPESA,
            PlanoConta.ClassificacaoDRE.DESPESA_OPERACIONAL,
            "CC",
        )
        titulo = self.criar_manual(plano, "f26p-fechada-cancelar")
        self.fechar()
        with self.assertRaises(ValidationError):
            cancelar_titulo_financeiro(titulo=titulo, usuario=self.usuario, motivo="Correcao controlada de teste")

    def test_baixa_nao_entra_na_validacao_economica(self):
        from pathlib import Path
        fonte = Path("financeiro/services.py").read_text(encoding="utf-8")
        bloco = fonte[
            fonte.index("def validar_fechamento_gerencial"):
            fonte.index("def fechar_competencia_gerencial")
        ]
        self.assertNotIn("BaixaFinanceira.objects", bloco)
