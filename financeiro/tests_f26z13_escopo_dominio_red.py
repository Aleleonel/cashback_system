from datetime import date
from decimal import Decimal

from django.core.exceptions import PermissionDenied
from django.test import TestCase

from accounts.models import PermissaoUsuario, Usuario
from accounts.permissions import PERMISSAO_FINANCEIRO_CANCELAR_LANCAMENTO, PERMISSAO_FINANCEIRO_EDITAR_LANCAMENTO
from empresas.models import Loja, Matriz
from financeiro.models import PlanoConta
from financeiro.services import atualizar_lancamento_manual, cancelar_titulo_financeiro, criar_lancamento_manual


class F26Z13EscopoDominioRED(TestCase):
    def setUp(self):
        self.matriz_a = Matriz.objects.create(nome="Matriz Z13 A", cnpj="31111111000191")
        self.matriz_b = Matriz.objects.create(nome="Matriz Z13 B", cnpj="32222222000191")
        self.loja_a1 = Loja.objects.create(matriz=self.matriz_a, nome="Loja Z13 A1")
        self.loja_a2 = Loja.objects.create(matriz=self.matriz_a, nome="Loja Z13 A2")
        self.loja_b1 = Loja.objects.create(matriz=self.matriz_b, nome="Loja Z13 B1")
        self.plano_a = PlanoConta.objects.create(matriz=self.matriz_a, codigo="Z13A", nome="Despesa Z13 A", natureza="DESPESA", classificacao_dre="DESPESA_OPERACIONAL", tipo=PlanoConta.Tipo.ANALITICA, aceita_lancamento=True)
        self.plano_b = PlanoConta.objects.create(matriz=self.matriz_b, codigo="Z13B", nome="Despesa Z13 B", natureza="DESPESA", classificacao_dre="DESPESA_OPERACIONAL", tipo=PlanoConta.Tipo.ANALITICA, aceita_lancamento=True)
        self.operador = Usuario.objects.create_user(username="operador_z13", password="x", matriz=self.matriz_a, perfil=Usuario.PERFIL_OPERADOR)
        self.operador.lojas.add(self.loja_a1)
        PermissaoUsuario.objects.create(usuario=self.operador, permissao=PERMISSAO_FINANCEIRO_EDITAR_LANCAMENTO)
        PermissaoUsuario.objects.create(usuario=self.operador, permissao=PERMISSAO_FINANCEIRO_CANCELAR_LANCAMENTO)
        self.admin = Usuario.objects.create_user(username="admin_z13", password="x", matriz=self.matriz_a, perfil=Usuario.PERFIL_ADMIN_LOJA)
        self.admin.lojas.add(self.loja_a1)

    def _titulo(self, matriz, loja, plano, chave):
        return criar_lancamento_manual(
            matriz=matriz, loja=loja, natureza="PAGAR", chave_idempotencia=chave,
            descricao="Titulo Z13", data_emissao=date(2026,11,1), data_competencia=date(2026,11,1),
            plano_conta=plano, centro_custo=None, entidade_nome="Fornecedor",
            documento_referencia=chave, valor_bruto=Decimal("100.00"),
            valor_desconto=Decimal("0.00"), valor_juros=Decimal("0.00"),
            parcelas=[{"numero":1,"vencimento":date(2026,11,10),"valor":Decimal("100.00")}],
            observacao="", usuario=self.admin,
        )

    def _editar(self, titulo, loja=None, plano=None):
        return atualizar_lancamento_manual(
            titulo=titulo, loja=loja if loja is not None else titulo.loja, natureza="PAGAR",
            descricao="Corrigido Z13", data_emissao=date(2026,11,1),
            parcelas=[{"numero":1,"vencimento":date(2026,11,10),"valor":Decimal("100.00")}],
            plano_conta=plano if plano is not None else titulo.plano_conta, centro_custo=None,
            entidade_nome="Fornecedor", documento_referencia="CORR-Z13",
            data_competencia=date(2026,11,1), valor_bruto=Decimal("100.00"),
            valor_desconto=Decimal("0.00"), valor_juros=Decimal("0.00"),
            observacao="", usuario=self.operador,
        )

    def test_01_operador_capability_nao_edita_titulo_outra_matriz(self):
        t=self._titulo(self.matriz_b,self.loja_b1,self.plano_b,"z13-m2-edit")
        with self.assertRaises(PermissionDenied):
            self._editar(t,loja=self.loja_b1,plano=self.plano_b)

    def test_02_operador_capability_nao_cancela_titulo_outra_matriz(self):
        t=self._titulo(self.matriz_b,self.loja_b1,self.plano_b,"z13-m2-cancel")
        with self.assertRaises(PermissionDenied):
            cancelar_titulo_financeiro(titulo=t,usuario=self.operador, motivo="Correcao controlada de teste")

    def test_03_operador_capability_nao_edita_loja_irma(self):
        t=self._titulo(self.matriz_a,self.loja_a2,self.plano_a,"z13-a2-edit")
        with self.assertRaises(PermissionDenied):
            self._editar(t)

    def test_04_operador_capability_nao_cancela_loja_irma(self):
        t=self._titulo(self.matriz_a,self.loja_a2,self.plano_a,"z13-a2-cancel")
        with self.assertRaises(PermissionDenied):
            cancelar_titulo_financeiro(titulo=t,usuario=self.operador, motivo="Correcao controlada de teste")

    def test_05_operador_capability_edita_propria_loja(self):
        t=self._titulo(self.matriz_a,self.loja_a1,self.plano_a,"z13-a1-edit")
        self._editar(t)
        t.refresh_from_db()
        self.assertEqual(t.documento_referencia,"CORR-Z13")

    def test_06_operador_capability_cancela_propria_loja(self):
        t=self._titulo(self.matriz_a,self.loja_a1,self.plano_a,"z13-a1-cancel")
        cancelar_titulo_financeiro(titulo=t,usuario=self.operador, motivo="Correcao controlada de teste")
        t.refresh_from_db()
        self.assertEqual(t.status,"CANCELADO")
