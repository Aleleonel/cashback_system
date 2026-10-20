from django.db import models
from django.test import SimpleTestCase

from financeiro.models import PlanoConta


class F25D4ClassificacaoDREContratoRedTests(SimpleTestCase):
    """
    Barreira arquitetural para a DRE.

    PlanoConta.natureza continua representando a natureza contabil ampla.
    classificacao_dre representa explicitamente a posicao economica da conta
    dentro da DRE, sem inferencia por nome, codigo ou texto livre.
    """

    def test_plano_conta_possui_classificacao_dre_explicita(self):
        campo = PlanoConta._meta.get_field("classificacao_dre")
        self.assertIsInstance(campo, models.CharField)
        self.assertTrue(campo.blank)
        self.assertTrue(campo.null)

    def test_classificacao_dre_possui_grupos_economicos_oficiais(self):
        campo = PlanoConta._meta.get_field("classificacao_dre")
        valores = {valor for valor, _rotulo in campo.choices}
        esperados = {
            "DEDUCAO_RECEITA",
            "DESPESA_OPERACIONAL",
            "RESULTADO_FINANCEIRO",
            "OUTRA_RECEITA_DESPESA",
        }
        self.assertEqual(valores, esperados)

    def test_classificacao_dre_nao_substitui_natureza_contabil(self):
        campos = {campo.name for campo in PlanoConta._meta.get_fields()}
        self.assertIn("natureza", campos)
        self.assertIn("classificacao_dre", campos)

    def test_classificacao_dre_e_opcional_para_contas_fora_da_dre(self):
        campo = PlanoConta._meta.get_field("classificacao_dre")
        self.assertTrue(campo.blank)
        self.assertTrue(campo.null)
        self.assertIsNone(campo.default)

    def test_classificacao_dre_nao_e_inferida_por_nome_ou_codigo(self):
        """
        O contrato deliberadamente exige um campo persistido.
        Este teste impede que a futura DRE dependa apenas de natureza/nome/codigo.
        """
        campo = PlanoConta._meta.get_field("classificacao_dre")
        self.assertEqual(campo.name, "classificacao_dre")