from datetime import date
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from auditoria.models import RegistroAuditoria
from core.choices import StatusOperacional
from empresas.models import Loja, Matriz
from financeiro.models import TituloFinanceiro
from financeiro.services import criar_titulo_financeiro


class OrigemTipoAuditoriaContractTest(TestCase):
    def setUp(self):
        self.matriz = Matriz.objects.create(nome="Matriz Financeiro K2")
        self.loja = Loja.objects.create(
            matriz=self.matriz,
            nome="Loja Financeiro K2",
            status=StatusOperacional.ATIVA,
        )
        self.usuario = get_user_model().objects.create_user(
            username="financeiro_k2",
            password="123456",
            matriz=self.matriz,
        )
        self.base = dict(
            matriz=self.matriz,
            loja=self.loja,
            natureza=TituloFinanceiro.Natureza.RECEBER,
            origem_tipo="MANUAL",
            origem_id="K2-1",
            chave_idempotencia="K2-1",
            descricao="Titulo manual K2",
            data_emissao=date(2026, 9, 14),
            parcelas=[{"numero": 1, "vencimento": date(2026, 10, 14), "valor": Decimal("100.00")}],
        )

    def test_origem_tipo_possui_enum_oficial(self):
        self.assertTrue(hasattr(TituloFinanceiro, "OrigemTipo"))
        self.assertEqual(
            set(TituloFinanceiro.OrigemTipo.values),
            {"COMPRA_RECEBIMENTO", "VENDA_PAGAMENTO", "MANUAL", "AJUSTE"},
        )

    def test_origem_tipo_invalida_e_rejeitada(self):
        dados = dict(self.base)
        dados["origem_tipo"] = "QUALQUER_TEXTO"
        with self.assertRaises(ValidationError):
            criar_titulo_financeiro(**dados)

    def test_criacao_registra_auditoria(self):
        titulo = criar_titulo_financeiro(**self.base, usuario=self.usuario)
        registro = RegistroAuditoria.objects.get(
            recurso="financeiro.titulo",
            recurso_id=str(titulo.uuid),
            acao=RegistroAuditoria.ACAO_CRIAR,
        )
        self.assertEqual(registro.matriz, self.matriz)
        self.assertEqual(registro.loja, self.loja)
        self.assertEqual(registro.usuario, self.usuario)

    def test_falha_auditoria_desfaz_criacao(self):
        with patch(
            "financeiro.services.registrar_auditoria",
            side_effect=RuntimeError("Falha simulada de auditoria"),
        ):
            with self.assertRaises(RuntimeError):
                criar_titulo_financeiro(**self.base, usuario=self.usuario)
        self.assertFalse(TituloFinanceiro.objects.filter(matriz=self.matriz, origem_id="K2-1").exists())

    def test_repeticao_idempotente_nao_duplica_auditoria(self):
        primeiro = criar_titulo_financeiro(**self.base, usuario=self.usuario)
        segundo = criar_titulo_financeiro(**self.base, usuario=self.usuario)
        self.assertEqual(primeiro.pk, segundo.pk)
        self.assertEqual(
            RegistroAuditoria.objects.filter(
                recurso="financeiro.titulo",
                recurso_id=str(primeiro.uuid),
                acao=RegistroAuditoria.ACAO_CRIAR,
            ).count(),
            1,
        )