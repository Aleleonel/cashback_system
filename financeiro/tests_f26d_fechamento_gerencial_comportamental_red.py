from datetime import date
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from empresas.models import Matriz
from financeiro.models import FechamentoGerencial
from financeiro.services import (
    fechar_competencia_gerencial,
    reabrir_competencia_gerencial,
    validar_fechamento_gerencial,
)


class F26DFechamentoGerencialComportamentalRED(TestCase):
    def setUp(self):
        self.matriz = Matriz.objects.create(nome="Matriz F26D", status="ativa")
        self.outra = Matriz.objects.create(nome="Outra Matriz F26D", status="ativa")
        U = get_user_model()
        self.admin = U.objects.create_superuser(
            username="f26d_admin", email="f26d@example.test", password="TesteF26D!"
        )
        if hasattr(self.admin, "ativo"):
            self.admin.ativo = True
            self.admin.save(update_fields=["ativo"])

    def test_fechamento_cria_competencia_fechada_com_autoria(self):
        f = fechar_competencia_gerencial(
            matriz=self.matriz, competencia_ano=2026, competencia_mes=7, usuario=self.admin
        )
        self.assertEqual(f.status, FechamentoGerencial.Status.FECHADO)
        self.assertEqual(f.matriz, self.matriz)
        self.assertEqual((f.competencia_ano, f.competencia_mes), (2026, 7))
        self.assertEqual(f.fechado_por, self.admin)
        self.assertIsNotNone(f.fechado_em)

    def test_fechamento_repetido_e_idempotente(self):
        a = fechar_competencia_gerencial(
            matriz=self.matriz, competencia_ano=2026, competencia_mes=7, usuario=self.admin
        )
        instante = a.fechado_em
        b = fechar_competencia_gerencial(
            matriz=self.matriz, competencia_ano=2026, competencia_mes=7, usuario=self.admin
        )
        self.assertEqual(a.pk, b.pk)
        self.assertEqual(FechamentoGerencial.objects.count(), 1)
        self.assertEqual(b.fechado_em, instante)

    def test_matrizes_distintas_podem_fechar_mesmo_periodo(self):
        a = fechar_competencia_gerencial(
            matriz=self.matriz, competencia_ano=2026, competencia_mes=7, usuario=self.admin
        )
        b = fechar_competencia_gerencial(
            matriz=self.outra, competencia_ano=2026, competencia_mes=7, usuario=self.admin
        )
        self.assertNotEqual(a.pk, b.pk)
        self.assertEqual(FechamentoGerencial.objects.count(), 2)

    def test_reabertura_exige_motivo(self):
        f = fechar_competencia_gerencial(
            matriz=self.matriz, competencia_ano=2026, competencia_mes=7, usuario=self.admin
        )
        with self.assertRaises(ValidationError):
            reabrir_competencia_gerencial(fechamento=f, usuario=self.admin, motivo="")

    def test_reabertura_registra_autoria_motivo_e_instante(self):
        f = fechar_competencia_gerencial(
            matriz=self.matriz, competencia_ano=2026, competencia_mes=7, usuario=self.admin
        )
        f = reabrir_competencia_gerencial(
            fechamento=f, usuario=self.admin, motivo="Ajuste contabil gerencial"
        )
        self.assertEqual(f.status, FechamentoGerencial.Status.ABERTO)
        self.assertEqual(f.reaberto_por, self.admin)
        self.assertEqual(f.motivo_reabertura, "Ajuste contabil gerencial")
        self.assertIsNotNone(f.reaberto_em)

    def test_nao_reabre_competencia_ja_aberta(self):
        f = FechamentoGerencial.objects.create(
            matriz=self.matriz, competencia_ano=2026, competencia_mes=7
        )
        with self.assertRaises(ValidationError):
            reabrir_competencia_gerencial(
                fechamento=f, usuario=self.admin, motivo="Tentativa indevida"
            )

    def test_validacao_rejeita_mes_invalido(self):
        r = validar_fechamento_gerencial(
            matriz=self.matriz, competencia_ano=2026, competencia_mes=13
        )
        self.assertFalse(r["valido"])
        self.assertTrue(r["erros"])

    def test_validacao_expoe_checklist_estruturado(self):
        r = validar_fechamento_gerencial(
            matriz=self.matriz, competencia_ano=2026, competencia_mes=7
        )
        self.assertIn("pendencias", r)
        self.assertIn("avisos", r)
        self.assertIn("itens", r)

    def test_checklist_tem_identificadores_estaveis(self):
        r = validar_fechamento_gerencial(
            matriz=self.matriz, competencia_ano=2026, competencia_mes=7
        )
        itens = r["itens"]
        self.assertTrue(itens)
        for item in itens:
            self.assertIn("codigo", item)
            self.assertIn("status", item)
            self.assertIn("bloqueante", item)

    def test_fechamento_recusa_checklist_com_pendencia_bloqueante(self):
        # O comportamento detalhado das pendencias sera implementado no proximo passo.
        # Este RED exige que fechar nunca ignore uma validacao bloqueante.
        from unittest.mock import patch
        retorno = {
            "valido": False,
            "erros": ["Pendencia bloqueante."],
            "pendencias": [{"codigo": "TESTE", "bloqueante": True}],
            "avisos": [],
            "itens": [{"codigo": "TESTE", "status": "PENDENTE", "bloqueante": True}],
        }
        with patch("financeiro.services.validar_fechamento_gerencial", return_value=retorno):
            with self.assertRaises(ValidationError):
                fechar_competencia_gerencial(
                    matriz=self.matriz,
                    competencia_ano=2026,
                    competencia_mes=7,
                    usuario=self.admin,
                )