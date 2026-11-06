from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from configuracoes.models import ConfiguracaoComercial
from empresas.models import Matriz


class F32BPoliticaAtacadoContratoTests(TestCase):
    """
    Contrato RED do F32B.

    Este arquivo descreve o nucleo esperado da Politica de Atacado:
    - configuracao por Matriz;
    - quantidade arbitraria de faixas;
    - faixa por valor minimo/maximo e percentual;
    - proibicao de sobreposicao/inconsistencia;
    - politica configuravel para produto promocional contar ou nao
      para atingir minimo/faixa;
    - produto promocional nao recebe automaticamente o desconto atacadista.

    A implementacao sera feita somente no proximo passo GREEN.
    """

    @classmethod
    def setUpTestData(cls):
        cls.matriz_a = Matriz.objects.create(
            nome="Matriz F32 A",
            cnpj="11111111000191",
        )
        cls.matriz_b = Matriz.objects.create(
            nome="Matriz F32 B",
            cnpj="22222222000191",
        )

    def test_configuracao_comercial_expoe_politica_promocional_para_enquadramento(self):
        field_names = {f.name for f in ConfiguracaoComercial._meta.get_fields()}
        self.assertIn(
            "produto_promocional_conta_para_faixa_atacado",
            field_names,
            "A Matriz deve poder decidir se produtos promocionais contam para atingir minimo/faixa.",
        )

    def test_modelo_de_faixa_atacado_existe(self):
        from configuracoes.models import FaixaAtacado

        self.assertIsNotNone(FaixaAtacado)

    def test_faixa_atacado_tem_campos_de_intervalo_percentual_e_configuracao(self):
        from configuracoes.models import FaixaAtacado

        fields = {f.name for f in FaixaAtacado._meta.get_fields()}
        for expected in (
            "configuracao",
            "valor_minimo",
            "valor_maximo",
            "percentual_desconto",
        ):
            self.assertIn(expected, fields)

    def test_configuracao_aceita_quantidade_arbitraria_de_faixas(self):
        from configuracoes.models import FaixaAtacado

        config = ConfiguracaoComercial.objects.create(
            matriz=self.matriz_a,
            atacado_ativo=True,
        )
        for minimo, maximo, percentual in (
            ("1000.00", "1999.99", "5.00"),
            ("2000.00", "4999.99", "8.00"),
            ("5000.00", None, "12.00"),
        ):
            FaixaAtacado.objects.create(
                configuracao=config,
                valor_minimo=Decimal(minimo),
                valor_maximo=None if maximo is None else Decimal(maximo),
                percentual_desconto=Decimal(percentual),
            )

        self.assertEqual(config.faixas_atacado.count(), 3)

    def test_faixa_rejeita_maximo_menor_que_minimo(self):
        from configuracoes.models import FaixaAtacado

        config = ConfiguracaoComercial.objects.create(
            matriz=self.matriz_a,
            atacado_ativo=True,
        )
        faixa = FaixaAtacado(
            configuracao=config,
            valor_minimo=Decimal("2000.00"),
            valor_maximo=Decimal("1000.00"),
            percentual_desconto=Decimal("5.00"),
        )
        with self.assertRaises(ValidationError):
            faixa.full_clean()

    def test_faixas_da_mesma_configuracao_nao_podem_sobrepor(self):
        from configuracoes.models import FaixaAtacado

        config = ConfiguracaoComercial.objects.create(
            matriz=self.matriz_a,
            atacado_ativo=True,
        )
        FaixaAtacado.objects.create(
            configuracao=config,
            valor_minimo=Decimal("1000.00"),
            valor_maximo=Decimal("2000.00"),
            percentual_desconto=Decimal("5.00"),
        )
        segunda = FaixaAtacado(
            configuracao=config,
            valor_minimo=Decimal("1500.00"),
            valor_maximo=Decimal("3000.00"),
            percentual_desconto=Decimal("8.00"),
        )
        with self.assertRaises(ValidationError):
            segunda.full_clean()

    def test_mesmos_intervalos_sao_permitidos_em_matrizes_diferentes(self):
        from configuracoes.models import FaixaAtacado

        config_a = ConfiguracaoComercial.objects.create(matriz=self.matriz_a, atacado_ativo=True)
        config_b = ConfiguracaoComercial.objects.create(matriz=self.matriz_b, atacado_ativo=True)

        FaixaAtacado.objects.create(
            configuracao=config_a,
            valor_minimo=Decimal("1000.00"),
            valor_maximo=Decimal("1999.99"),
            percentual_desconto=Decimal("5.00"),
        )
        FaixaAtacado.objects.create(
            configuracao=config_b,
            valor_minimo=Decimal("1000.00"),
            valor_maximo=Decimal("1999.99"),
            percentual_desconto=Decimal("10.00"),
        )

        self.assertEqual(FaixaAtacado.objects.count(), 2)

    def test_servico_enquadra_valor_na_faixa_correta(self):
        from configuracoes.models import FaixaAtacado
        from configuracoes.services_atacado import obter_faixa_atacado

        config = ConfiguracaoComercial.objects.create(matriz=self.matriz_a, atacado_ativo=True)
        FaixaAtacado.objects.create(
            configuracao=config,
            valor_minimo=Decimal("1000.00"),
            valor_maximo=Decimal("1999.99"),
            percentual_desconto=Decimal("5.00"),
        )
        FaixaAtacado.objects.create(
            configuracao=config,
            valor_minimo=Decimal("2000.00"),
            valor_maximo=None,
            percentual_desconto=Decimal("8.00"),
        )

        faixa = obter_faixa_atacado(config, Decimal("2500.00"))
        self.assertEqual(faixa.percentual_desconto, Decimal("8.00"))

    def test_servico_nao_enquadra_valor_abaixo_do_minimo(self):
        from configuracoes.models import FaixaAtacado
        from configuracoes.services_atacado import obter_faixa_atacado

        config = ConfiguracaoComercial.objects.create(matriz=self.matriz_a, atacado_ativo=True)
        FaixaAtacado.objects.create(
            configuracao=config,
            valor_minimo=Decimal("1000.00"),
            valor_maximo=None,
            percentual_desconto=Decimal("5.00"),
        )

        self.assertIsNone(obter_faixa_atacado(config, Decimal("999.99")))

    def test_regra_promocional_conta_para_enquadramento_quando_matriz_habilita(self):
        from configuracoes.services_atacado import calcular_base_enquadramento_atacado

        config = ConfiguracaoComercial.objects.create(
            matriz=self.matriz_a,
            atacado_ativo=True,
            produto_promocional_conta_para_faixa_atacado=True,
        )
        base = calcular_base_enquadramento_atacado(
            config=config,
            valor_itens_elegiveis=Decimal("800.00"),
            valor_itens_promocionais=Decimal("300.00"),
        )
        self.assertEqual(base, Decimal("1100.00"))

    def test_regra_promocional_nao_conta_para_enquadramento_quando_matriz_desabilita(self):
        from configuracoes.services_atacado import calcular_base_enquadramento_atacado

        config = ConfiguracaoComercial.objects.create(
            matriz=self.matriz_a,
            atacado_ativo=True,
            produto_promocional_conta_para_faixa_atacado=False,
        )
        base = calcular_base_enquadramento_atacado(
            config=config,
            valor_itens_elegiveis=Decimal("800.00"),
            valor_itens_promocionais=Decimal("300.00"),
        )
        self.assertEqual(base, Decimal("800.00"))

    def test_desconto_atacado_incide_apenas_sobre_base_elegivel(self):
        from configuracoes.services_atacado import calcular_desconto_atacado

        desconto = calcular_desconto_atacado(
            valor_elegivel=Decimal("800.00"),
            percentual=Decimal("5.00"),
        )
        self.assertEqual(desconto, Decimal("40.00"))

    def test_produto_promocional_nao_entra_na_base_de_desconto_atacado(self):
        from configuracoes.services_atacado import calcular_desconto_atacado

        # Mesmo que R$ 300 promocionais possam contar para ENQUADRAMENTO,
        # o desconto atacadista deve incidir apenas sobre R$ 800 elegiveis.
        desconto = calcular_desconto_atacado(
            valor_elegivel=Decimal("800.00"),
            percentual=Decimal("5.00"),
        )
        self.assertNotEqual(desconto, Decimal("55.00"))
        self.assertEqual(desconto, Decimal("40.00"))