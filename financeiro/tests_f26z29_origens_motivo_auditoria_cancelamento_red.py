from datetime import date
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.test import TestCase
from accounts.models import PermissaoUsuario, Usuario
from accounts.permissions import PERMISSAO_FINANCEIRO_CANCELAR_LANCAMENTO
from auditoria.models import RegistroAuditoria
from empresas.models import Loja, Matriz
from financeiro.models import TituloFinanceiro
from financeiro.services import cancelar_titulo_financeiro, criar_titulo_financeiro

class F26Z29CancelamentoSemanticaTests(TestCase):
    def setUp(self):
        self.m=Matriz.objects.create(nome="Matriz F26Z29",cnpj="29292929000191")
        self.l=Loja.objects.create(matriz=self.m,nome="Loja F26Z29")
        self.u=Usuario.objects.create_user(username="f26z29",password="x",matriz=self.m,perfil=Usuario.PERFIL_OPERADOR)
        self.u.lojas.add(self.l)
        PermissaoUsuario.objects.create(usuario=self.u,permissao=PERMISSAO_FINANCEIRO_CANCELAR_LANCAMENTO)
    def titulo(self, origem, chave):
        return criar_titulo_financeiro(matriz=self.m,loja=self.l,natureza=TituloFinanceiro.Natureza.PAGAR,
            origem_tipo=origem,origem_id=chave,chave_idempotencia=chave,descricao="F26Z29",
            data_emissao=date(2026,11,1),parcelas=[{"numero":1,"vencimento":date(2026,11,10),"valor":Decimal("10.00")}],usuario=None)
    def test_01_manual_exige_motivo(self):
        t=self.titulo(TituloFinanceiro.OrigemTipo.MANUAL,"z29-01")
        with self.assertRaises(ValidationError): cancelar_titulo_financeiro(titulo=t,usuario=self.u,motivo="")
    def test_02_manual_com_motivo_cancela_e_audita_motivo(self):
        t=self.titulo(TituloFinanceiro.OrigemTipo.MANUAL,"z29-02")
        cancelar_titulo_financeiro(titulo=t,usuario=self.u,motivo="Lancamento criado em duplicidade.")
        t.refresh_from_db(); self.assertEqual(t.status,TituloFinanceiro.Status.CANCELADO)
        a=RegistroAuditoria.objects.filter(recurso="financeiro.titulo",recurso_id=str(t.uuid)).order_by("-criado_em").first()
        self.assertIsNotNone(a); self.assertIn("Lancamento criado em duplicidade.",a.descricao)
    def test_03_compra_recebimento_nao_cancela_diretamente(self):
        t=self.titulo(TituloFinanceiro.OrigemTipo.COMPRA_RECEBIMENTO,"z29-03")
        with self.assertRaises(ValidationError): cancelar_titulo_financeiro(titulo=t,usuario=self.u,motivo="Correcao")
    def test_04_venda_pagamento_nao_cancela_diretamente(self):
        t=self.titulo(TituloFinanceiro.OrigemTipo.VENDA_PAGAMENTO,"z29-04")
        with self.assertRaises(ValidationError): cancelar_titulo_financeiro(titulo=t,usuario=self.u,motivo="Correcao")
    def test_05_comissao_nao_cancela_diretamente(self):
        t=self.titulo(TituloFinanceiro.OrigemTipo.COMISSAO,"z29-05")
        with self.assertRaises(ValidationError): cancelar_titulo_financeiro(titulo=t,usuario=self.u,motivo="Correcao")
    def test_06_cancelado_idempotente_nao_gera_segunda_auditoria(self):
        t=self.titulo(TituloFinanceiro.OrigemTipo.MANUAL,"z29-06")
        cancelar_titulo_financeiro(titulo=t,usuario=self.u,motivo="Erro inicial")
        n=RegistroAuditoria.objects.filter(recurso="financeiro.titulo",recurso_id=str(t.uuid)).count()
        cancelar_titulo_financeiro(titulo=t,usuario=self.u,motivo="Tentativa repetida")
        self.assertEqual(RegistroAuditoria.objects.filter(recurso="financeiro.titulo",recurso_id=str(t.uuid)).count(),n)
