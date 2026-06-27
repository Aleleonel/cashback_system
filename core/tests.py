from django.test import SimpleTestCase


class SanityTest(SimpleTestCase):

    def test_ambiente_de_testes_funciona(self):
        self.assertEqual(1 + 1, 2)