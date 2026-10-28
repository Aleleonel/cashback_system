from datetime import date
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

from accounts.models import PermissaoUsuario, Usuario
from accounts.permissions import PERMISSAO_FINANCEIRO_CANCELAR_LANCAMENTO
from empresas.models import Loja, Matriz
from financeiro.models import BaixaFinanceira, ParcelaFinanceira, TituloFinanceiro
from financeiro.services import (
    cancelar_titulo_financeiro,
    criar_titulo_financeiro,
    estornar_baixa_financeira,
    registrar_baixa_financeira,
)


class F26Z27CancelamentoBaixasEstornosTests(TestCase):
    def setUp(self):
        self.matriz = Matriz.objects.create(nome="Matriz F26Z27", cnpj="27272727000191")
        self.loja = Loja.objects.create(matriz=self.matriz, nome="Loja F26Z27")
        self.user = Usuario.objects.create_user(
            username="f26z27", password="teste123", matriz=self.matriz,
            perfil=Usuario.PERFIL_OPERADOR,
        )
        self.user.lojas.add(self.loja)
        PermissaoUsuario.objects.create(
            usuario=self.user, permissao=PERMISSAO_FINANCEIRO_CANCELAR_LANCAMENTO
        )

    def titulo(self, chave):
        return criar_titulo_financeiro(
            matriz=self.matriz, loja=self.loja,
            natureza=TituloFinanceiro.Natureza.PAGAR,
            origem_tipo=TituloFinanceiro.OrigemTipo.MANUAL,
            origem_id=chave, chave_idempotencia=chave,
            descricao="F26Z27", data_emissao=date(2026, 11, 1),
            parcelas=[{"numero": 1, "vencimento": date(2026, 11, 10), "valor": Decimal("100.00")}],
            usuario=None,
        )

    def baixa(self, titulo, valor, chave):
        return registrar_baixa_financeira(
            parcela=titulo.parcelas.get(numero=1), valor=valor,
            data=date(2026, 11, 2), chave_idempotencia=chave,
            usuario=self.user,
        )

    def test_01_baixa_ativa_bloqueia_cancelamento(self):
        t=self.titulo("f26z27-01"); self.baixa(t, Decimal("100.00"), "b01")
        with self.assertRaises(ValidationError):
            cancelar_titulo_financeiro(titulo=t, usuario=self.user, motivo="Correcao controlada de teste")
        t.refresh_from_db()
        self.assertNotEqual(t.status, TituloFinanceiro.Status.CANCELADO)

    def test_02_estorno_parcial_ainda_bloqueia_cancelamento(self):
        t=self.titulo("f26z27-02"); b=self.baixa(t, Decimal("100.00"), "b02")
        estornar_baixa_financeira(
            baixa=b, valor=Decimal("40.00"), data=date(2026,11,3),
            chave_idempotencia="e02", usuario=self.user,
        )
        with self.assertRaises(ValidationError):
            cancelar_titulo_financeiro(titulo=t, usuario=self.user, motivo="Correcao controlada de teste")

    def test_03_baixa_totalmente_estornada_permite_cancelar_preservando_eventos(self):
        t=self.titulo("f26z27-03"); b=self.baixa(t, Decimal("100.00"), "b03")
        e=estornar_baixa_financeira(
            baixa=b, valor=Decimal("100.00"), data=date(2026,11,3),
            chave_idempotencia="e03", usuario=self.user,
        )
        ids=list(BaixaFinanceira.objects.filter(parcela__titulo=t).values_list("pk",flat=True))
        cancelar_titulo_financeiro(titulo=t, usuario=self.user, motivo="Correcao controlada de teste")
        t.refresh_from_db(); p=t.parcelas.get(numero=1)
        self.assertEqual(t.status, TituloFinanceiro.Status.CANCELADO)
        self.assertEqual(p.status, ParcelaFinanceira.Status.CANCELADO)
        self.assertEqual(list(BaixaFinanceira.objects.filter(parcela__titulo=t).values_list("pk",flat=True)),ids)
        self.assertTrue(BaixaFinanceira.objects.filter(pk=b.pk).exists())
        self.assertEqual(BaixaFinanceira.objects.get(pk=e.pk).baixa_estornada_id,b.pk)

    def test_04_cancelamento_sem_eventos_preserva_fluxo_normal(self):
        t=self.titulo("f26z27-04")
        cancelar_titulo_financeiro(titulo=t, usuario=self.user, motivo="Correcao controlada de teste")
        t.refresh_from_db()
        self.assertEqual(t.status, TituloFinanceiro.Status.CANCELADO)

    def test_05_cancelamento_idempotente_nao_duplica_eventos_financeiros(self):
        t=self.titulo("f26z27-05")
        cancelar_titulo_financeiro(titulo=t, usuario=self.user, motivo="Correcao controlada de teste")
        qtd=BaixaFinanceira.objects.filter(parcela__titulo=t).count()
        cancelar_titulo_financeiro(titulo=t, usuario=self.user, motivo="Correcao controlada de teste")
        self.assertEqual(BaixaFinanceira.objects.filter(parcela__titulo=t).count(),qtd)

    def test_06_soma_global_zero_nao_pode_mascarar_saldo_ativo_em_uma_parcela(self):
        t=criar_titulo_financeiro(
            matriz=self.matriz, loja=self.loja,
            natureza=TituloFinanceiro.Natureza.PAGAR,
            origem_tipo=TituloFinanceiro.OrigemTipo.MANUAL,
            origem_id="f26z27-06", chave_idempotencia="f26z27-06",
            descricao="F26Z27 multi", data_emissao=date(2026,11,1),
            parcelas=[
                {"numero":1,"vencimento":date(2026,11,10),"valor":Decimal("100.00")},
                {"numero":2,"vencimento":date(2026,11,20),"valor":Decimal("100.00")},
            ], usuario=None,
        )
        p1=t.parcelas.get(numero=1); p2=t.parcelas.get(numero=2)
        b1=registrar_baixa_financeira(parcela=p1,valor=Decimal("100.00"),data=date(2026,11,2),chave_idempotencia="b061",usuario=self.user)
        # Contrato: eventos de cada parcela devem ser conciliados individualmente.
        estornar_baixa_financeira(baixa=b1,valor=Decimal("100.00"),data=date(2026,11,3),chave_idempotencia="e061",usuario=self.user)
        registrar_baixa_financeira(parcela=p2,valor=Decimal("50.00"),data=date(2026,11,4),chave_idempotencia="b062",usuario=self.user)
        with self.assertRaises(ValidationError):
            cancelar_titulo_financeiro(titulo=t, usuario=self.user, motivo="Correcao controlada de teste")
