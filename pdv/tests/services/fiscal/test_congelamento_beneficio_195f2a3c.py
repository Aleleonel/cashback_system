from types import SimpleNamespace

from django.test import SimpleTestCase

from pdv.services.fiscal.snapshot_venda import (
    _memoria_regra_beneficio,
)


class CongelamentoBeneficio195F2A3CTests(SimpleTestCase):

    def test_extrai_dados_congelados_da_memoria_do_motor(self):
        resultado = SimpleNamespace(
            memoria_calculo={
                "regra": {
                    "beneficio_fiscal": "BEN-001",
                    "beneficio_fiscal_tipo": "desoneracao",
                    "beneficio_fiscal_descricao": "Teste",
                    "beneficio_exige_motivo_desoneracao": True,
                    "beneficio_motivo_desoneracao": "3",
                }
            }
        )

        dados = _memoria_regra_beneficio(resultado)

        self.assertEqual(dados["tipo"], "desoneracao")
        self.assertTrue(dados["exige_motivo"])
        self.assertEqual(dados["motivo"], "3")

    def test_sem_beneficio_gera_defaults_neutros(self):
        resultado = SimpleNamespace(
            memoria_calculo={"regra": {}}
        )

        dados = _memoria_regra_beneficio(resultado)

        self.assertEqual(dados["tipo"], "")
        self.assertFalse(dados["exige_motivo"])
        self.assertEqual(dados["motivo"], "")

    def test_memoria_ausente_gera_defaults_neutros(self):
        resultado = SimpleNamespace(
            memoria_calculo={}
        )

        dados = _memoria_regra_beneficio(resultado)

        self.assertEqual(
            dados,
            {
                "tipo": "",
                "exige_motivo": False,
                "motivo": "",
            },
        )