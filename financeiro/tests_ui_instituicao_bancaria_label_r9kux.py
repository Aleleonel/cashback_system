from django.test import SimpleTestCase
from financeiro.models import InstituicaoBancaria

class InstituicaoBancariaLabelR9KUXTests(SimpleTestCase):
    def test_str_com_codigo_bacen(self):
        instituicao = InstituicaoBancaria(codigo_bacen="341", nome="Banco Exemplo")
        self.assertEqual(str(instituicao), "341 - Banco Exemplo")

    def test_str_sem_codigo_bacen(self):
        instituicao = InstituicaoBancaria(codigo_bacen=None, nome="Banco Exemplo")
        self.assertEqual(str(instituicao), "Banco Exemplo")

    def test_str_com_codigo_bacen_vazio(self):
        instituicao = InstituicaoBancaria(codigo_bacen="", nome="Banco Exemplo")
        self.assertEqual(str(instituicao), "Banco Exemplo")