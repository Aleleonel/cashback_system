from datetime import date
from decimal import Decimal

from django.core.exceptions import PermissionDenied
from django.test import TestCase

from accounts.models import PermissaoUsuario, Usuario
from accounts.permissions import (
    PERMISSAO_FINANCEIRO_CANCELAR_LANCAMENTO,
    PERMISSAO_FINANCEIRO_EDITAR_LANCAMENTO,
)
from empresas.models import Loja, Matriz
from financeiro.models import ParcelaFinanceira, PlanoConta, TituloFinanceiro
from financeiro.services import atualizar_lancamento_manual, cancelar_titulo_financeiro


class F26Z10AutorizacaoDominioRED(TestCase):
    def setUp(self):
        self.matriz=Matriz.objects.create(nome="Matriz Z10")
        self.loja=Loja.objects.create(matriz=self.matriz,nome="Loja Z10")
        self.user=Usuario.objects.create_user(username="op_z10",password="x",perfil=Usuario.PERFIL_OPERADOR,matriz=self.matriz)
        self.plano=PlanoConta.objects.create(matriz=self.matriz,codigo="Z10",nome="Despesa Z10",natureza="DESPESA",classificacao_dre="DESPESA_OPERACIONAL")
        self.user.lojas.add(self.loja)

    def titulo(self):
        t=TituloFinanceiro.objects.create(
            matriz=self.matriz,loja=self.loja,natureza="PAGAR",
            origem_tipo="MANUAL",data_emissao=date(2026,11,1),
            valor_original=Decimal("100.00"),
            data_competencia=date(2026,11,1),valor_bruto=Decimal("100.00"),
            descricao="Original",
        )
        ParcelaFinanceira.objects.create(titulo=t,numero=1,vencimento=date(2026,11,10),valor_original=Decimal("100.00"))
        return t

    def payload(self,t):
        return dict(
            titulo=t,usuario=self.user,loja=self.loja,natureza=t.natureza,
            plano_conta=self.plano,centro_custo=None,data_emissao=t.data_emissao,
            data_competencia=t.data_competencia,valor_bruto=Decimal("120.00"),
            valor_desconto=Decimal("0.00"),valor_juros=Decimal("0.00"),descricao="Corrigido",
            entidade_nome="",documento_referencia="",observacao="",
            parcelas=[{"numero":1,"vencimento":date(2026,11,10),"valor":Decimal("120.00")}],
        )

    def test_01_edicao_sem_capability_e_bloqueada_no_servico(self):
        t=self.titulo()
        with self.assertRaises(PermissionDenied):
            atualizar_lancamento_manual(**self.payload(t))
        t.refresh_from_db()
        self.assertEqual(t.valor_bruto,Decimal("100.00"))

    def test_02_edicao_com_capability_e_permitida_no_servico(self):
        t=self.titulo()
        PermissaoUsuario.objects.create(usuario=self.user,permissao=PERMISSAO_FINANCEIRO_EDITAR_LANCAMENTO)
        atualizar_lancamento_manual(**self.payload(t))
        t.refresh_from_db()
        self.assertEqual(t.valor_bruto,Decimal("120.00"))

    def test_03_cancelamento_sem_capability_e_bloqueado_no_servico(self):
        t=self.titulo()
        with self.assertRaises(PermissionDenied):
            cancelar_titulo_financeiro(titulo=t,usuario=self.user, motivo="Correcao controlada de teste")
        t.refresh_from_db()
        self.assertNotEqual(t.status,"CANCELADO")

    def test_04_cancelamento_com_capability_e_permitido_no_servico(self):
        t=self.titulo()
        PermissaoUsuario.objects.create(usuario=self.user,permissao=PERMISSAO_FINANCEIRO_CANCELAR_LANCAMENTO)
        cancelar_titulo_financeiro(titulo=t,usuario=self.user, motivo="Correcao controlada de teste")
        t.refresh_from_db()
        self.assertEqual(t.status,"CANCELADO")

    def test_05_capability_editar_nao_autoriza_cancelar(self):
        t=self.titulo()
        PermissaoUsuario.objects.create(usuario=self.user,permissao=PERMISSAO_FINANCEIRO_EDITAR_LANCAMENTO)
        with self.assertRaises(PermissionDenied):
            cancelar_titulo_financeiro(titulo=t,usuario=self.user, motivo="Correcao controlada de teste")

    def test_06_capability_cancelar_nao_autoriza_editar(self):
        t=self.titulo()
        PermissaoUsuario.objects.create(usuario=self.user,permissao=PERMISSAO_FINANCEIRO_CANCELAR_LANCAMENTO)
        with self.assertRaises(PermissionDenied):
            atualizar_lancamento_manual(**self.payload(t))
