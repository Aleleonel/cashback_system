from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

from empresas.models import Matriz

from configuracoes.models import ConfiguracaoComercial
from configuracoes.selectors import get_configuracao_comercial
from configuracoes.services import (
    atualizar_configuracao_comercial,
    obter_ou_criar_configuracao_comercial,
)


class ConfiguracaoComercialModelTests(TestCase):
    def setUp(self):
        self.matriz = Matriz.objects.create(nome="Matriz CFG-01.1")

    def test_configuracao_possui_defaults_seguros(self):
        configuracao = ConfiguracaoComercial.objects.create(matriz=self.matriz)

        self.assertFalse(configuracao.atacado_ativo)
        self.assertEqual(
            configuracao.pedido_minimo_atacado,
            Decimal("0.00"),
        )
        self.assertEqual(
            configuracao.desconto_atacado_percentual,
            Decimal("0.00"),
        )
        self.assertTrue(configuracao.cashback_ativo)
        self.assertTrue(configuracao.voucher_ativo)

    def test_existe_apenas_uma_configuracao_por_matriz(self):
        primeira = obter_ou_criar_configuracao_comercial(matriz=self.matriz)
        segunda = obter_ou_criar_configuracao_comercial(matriz=self.matriz)

        self.assertEqual(primeira.pk, segunda.pk)
        self.assertEqual(
            ConfiguracaoComercial.objects.filter(matriz=self.matriz).count(),
            1,
        )

    def test_nao_aceita_desconto_acima_de_cem(self):
        configuracao = ConfiguracaoComercial(
            matriz=self.matriz,
            desconto_atacado_percentual=Decimal("101.00"),
        )

        with self.assertRaises(ValidationError):
            configuracao.full_clean()

    def test_nao_aceita_pedido_minimo_negativo(self):
        configuracao = ConfiguracaoComercial(
            matriz=self.matriz,
            pedido_minimo_atacado=Decimal("-1.00"),
        )

        with self.assertRaises(ValidationError):
            configuracao.full_clean()


class ConfiguracaoComercialServiceSelectorTests(TestCase):
    def setUp(self):
        self.matriz = Matriz.objects.create(nome="Matriz Services CFG-01.1")

    def test_selector_retorna_none_sem_configuracao(self):
        self.assertIsNone(get_configuracao_comercial(matriz=self.matriz))

    def test_service_cria_e_selector_localiza(self):
        criada = obter_ou_criar_configuracao_comercial(matriz=self.matriz)
        localizada = get_configuracao_comercial(matriz=self.matriz)

        self.assertEqual(criada.pk, localizada.pk)

    def test_service_atualiza_somente_campos_permitidos(self):
        configuracao = obter_ou_criar_configuracao_comercial(matriz=self.matriz)

        atualizar_configuracao_comercial(
            configuracao=configuracao,
            dados={
                "atacado_ativo": True,
                "pedido_minimo_atacado": Decimal("750.00"),
                "desconto_atacado_percentual": Decimal("20.00"),
                "matriz": None,
            },
        )

        configuracao.refresh_from_db()

        self.assertTrue(configuracao.atacado_ativo)
        self.assertEqual(
            configuracao.pedido_minimo_atacado,
            Decimal("750.00"),
        )
        self.assertEqual(
            configuracao.desconto_atacado_percentual,
            Decimal("20.00"),
        )
        self.assertEqual(configuracao.matriz, self.matriz)
