from django.test import SimpleTestCase

from core.templatetags.ui_tags import (
    cpf,
    money,
    telefone,
)


class UITagsTest(SimpleTestCase):

    def test_money_formata_valor_brasileiro(self):
        self.assertEqual(
            money('1234.5'),
            '1.234,50'
        )

    def test_cpf_formata_numero(self):
        self.assertEqual(
            cpf('12345678900'),
            '123.456.789-00'
        )

    def test_telefone_formata_celular(self):
        self.assertEqual(
            telefone('11999999999'),
            '(11) 99999-9999'
        )