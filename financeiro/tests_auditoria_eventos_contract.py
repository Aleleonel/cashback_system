from datetime import date
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from auditoria.models import RegistroAuditoria
from empresas.models import Matriz
from financeiro.models import BaixaFinanceira, ParcelaFinanceira, TituloFinanceiro
from financeiro.services import (
    cancelar_titulo_financeiro,
    criar_titulo_financeiro,
    estornar_baixa_financeira,
    registrar_baixa_financeira,
)


class AuditoriaEventosFinanceirosContractTest(TestCase):
    def setUp(self):
        self.matriz = Matriz.objects.create(nome="Matriz Auditoria Eventos")
        self.usuario = get_user_model().objects.create_user(
            username="financeiro_eventos",
            password="123456",
            matriz=self.matriz,
        )
        self.titulo = criar_titulo_financeiro(
            matriz=self.matriz,
            loja=None,
            natureza=TituloFinanceiro.Natureza.RECEBER,
            origem_tipo=TituloFinanceiro.OrigemTipo.MANUAL,
            origem_id="AUD-EVT-1",
            chave_idempotencia="AUD-EVT-1",
            descricao="Titulo auditoria eventos",
            data_emissao=date(2026, 9, 14),
            parcelas=[{"numero": 1, "vencimento": date(2026, 10, 14), "valor": Decimal("100.00")}],
            usuario=self.usuario,
        )
        self.parcela = self.titulo.parcelas.get(numero=1)

    def test_baixa_registra_auditoria(self):
        baixa = registrar_baixa_financeira(
            parcela=self.parcela, valor=Decimal("20.00"), data=date(2026, 9, 14),
            chave_idempotencia="AUD-BX-1", usuario=self.usuario,
        )
        self.assertTrue(RegistroAuditoria.objects.filter(
            recurso="financeiro.baixa", recurso_id=str(baixa.pk),
            acao=RegistroAuditoria.ACAO_CRIAR, usuario=self.usuario,
        ).exists())

    def test_estorno_registra_auditoria(self):
        baixa = registrar_baixa_financeira(
            parcela=self.parcela, valor=Decimal("20.00"), data=date(2026, 9, 14),
            chave_idempotencia="AUD-BX-2", usuario=self.usuario,
        )
        estorno = estornar_baixa_financeira(
            baixa=baixa, valor=Decimal("20.00"), data=date(2026, 9, 15),
            chave_idempotencia="AUD-EST-2", usuario=self.usuario,
        )
        self.assertTrue(RegistroAuditoria.objects.filter(
            recurso="financeiro.estorno", recurso_id=str(estorno.pk),
            acao=RegistroAuditoria.ACAO_CRIAR, usuario=self.usuario,
        ).exists())

    def test_cancelamento_registra_auditoria(self):
        cancelar_titulo_financeiro(titulo=self.titulo, usuario=self.usuario)
        self.assertTrue(RegistroAuditoria.objects.filter(
            recurso="financeiro.titulo", recurso_id=str(self.titulo.uuid),
            acao=RegistroAuditoria.ACAO_EDITAR, usuario=self.usuario,
        ).exists())

    def test_falha_auditoria_desfaz_baixa(self):
        with patch("financeiro.services.registrar_auditoria", side_effect=RuntimeError("falha auditoria")):
            with self.assertRaises(RuntimeError):
                registrar_baixa_financeira(
                    parcela=self.parcela, valor=Decimal("20.00"), data=date(2026, 9, 14),
                    chave_idempotencia="AUD-BX-ROLLBACK", usuario=self.usuario,
                )
        self.parcela.refresh_from_db()
        self.titulo.refresh_from_db()
        self.assertEqual(BaixaFinanceira.objects.filter(chave_idempotencia="AUD-BX-ROLLBACK").count(), 0)
        self.assertEqual(self.parcela.status, ParcelaFinanceira.Status.ABERTO)
        self.assertEqual(self.titulo.status, TituloFinanceiro.Status.ABERTO)

    def test_falha_auditoria_desfaz_estorno(self):
        baixa = registrar_baixa_financeira(
            parcela=self.parcela, valor=Decimal("20.00"), data=date(2026, 9, 14),
            chave_idempotencia="AUD-BX-3", usuario=self.usuario,
        )
        with patch("financeiro.services.registrar_auditoria", side_effect=RuntimeError("falha auditoria")):
            with self.assertRaises(RuntimeError):
                estornar_baixa_financeira(
                    baixa=baixa, valor=Decimal("20.00"), data=date(2026, 9, 15),
                    chave_idempotencia="AUD-EST-ROLLBACK", usuario=self.usuario,
                )
        self.assertEqual(BaixaFinanceira.objects.filter(chave_idempotencia="AUD-EST-ROLLBACK").count(), 0)

    def test_falha_auditoria_desfaz_cancelamento(self):
        with patch("financeiro.services.registrar_auditoria", side_effect=RuntimeError("falha auditoria")):
            with self.assertRaises(RuntimeError):
                cancelar_titulo_financeiro(titulo=self.titulo, usuario=self.usuario)
        self.titulo.refresh_from_db()
        self.parcela.refresh_from_db()
        self.assertEqual(self.titulo.status, TituloFinanceiro.Status.ABERTO)
        self.assertEqual(self.parcela.status, ParcelaFinanceira.Status.ABERTO)

    def test_repeticao_idempotente_baixa_nao_duplica_auditoria(self):
        kwargs=dict(
            parcela=self.parcela, valor=Decimal("20.00"), data=date(2026, 9, 14),
            chave_idempotencia="AUD-BX-IDEM", usuario=self.usuario,
        )
        baixa1=registrar_baixa_financeira(**kwargs)
        baixa2=registrar_baixa_financeira(**kwargs)
        self.assertEqual(baixa1.pk, baixa2.pk)
        self.assertEqual(RegistroAuditoria.objects.filter(
            recurso="financeiro.baixa", recurso_id=str(baixa1.pk),
            acao=RegistroAuditoria.ACAO_CRIAR,
        ).count(), 1)