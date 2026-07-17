from dataclasses import FrozenInstanceError

from django.test import SimpleTestCase

from estoque.services import ResultadoReservaEstoque


class ResultadoReservaEstoqueTestCase(SimpleTestCase):
    def test_armazena_reserva_e_estado_de_duplicidade(self):
        reserva = object()

        resultado = ResultadoReservaEstoque(
            reserva=reserva,
            duplicada=True,
        )

        self.assertIs(resultado.reserva, reserva)
        self.assertTrue(resultado.duplicada)

    def test_duplicada_e_falso_por_padrao(self):
        resultado = ResultadoReservaEstoque(
            reserva=object(),
        )

        self.assertFalse(resultado.duplicada)

    def test_resultado_e_imutavel(self):
        resultado = ResultadoReservaEstoque(
            reserva=object(),
        )

        with self.assertRaises(FrozenInstanceError):
            resultado.duplicada = True