from django.test import SimpleTestCase
from financeiro.models import CentroCusto

class CentroCustoLabelR9KUXTests(SimpleTestCase):
    def test_str_retorna_codigo_hifen_nome(self):
        centro = CentroCusto(codigo="ADM", nome="Administrativo")
        self.assertEqual(str(centro), "ADM - Administrativo")