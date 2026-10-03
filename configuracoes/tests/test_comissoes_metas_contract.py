from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

from empresas.models import Loja, Matriz
from configuracoes.models import ConfiguracaoComissaoMatriz, MetaComissaoLoja


class ComissoesMetasDominioContractTests(TestCase):
    """Contrato persistente F2D: polÃ­tica da matriz e N faixas por loja."""

    def setUp(self):
        self.matriz = Matriz.objects.create(nome="Matriz F2D")
        self.loja = Loja.objects.create(matriz=self.matriz, nome="Loja F2D")

    def test_politica_elegibilidade_individual_e_configuravel_por_matriz(self):
        cfg = ConfiguracaoComissaoMatriz.objects.create(
            matriz=self.matriz,
            exigir_minimo_individual=True,
            minimo_vendas_vendedor=Decimal("10000.00"),
        )
        self.assertTrue(cfg.exigir_minimo_individual)
        self.assertEqual(cfg.minimo_vendas_vendedor, Decimal("10000.00"))

        cfg.exigir_minimo_individual = False
        cfg.full_clean()
        cfg.save(update_fields=["exigir_minimo_individual", "atualizada_em"])
        cfg.refresh_from_db()
        self.assertFalse(cfg.exigir_minimo_individual)

    def test_loja_aceita_n_faixas_de_meta_com_percentuais_independentes(self):
        metas = [
            ("50000.00", "1.50"),
            ("70000.00", "3.00"),
            ("100000.00", "6.00"),
            ("150000.00", "8.00"),
        ]
        for valor_meta, percentual in metas:
            MetaComissaoLoja.objects.create(
                loja=self.loja,
                valor_meta=Decimal(valor_meta),
                percentual_comissao=Decimal(percentual),
            )

        cadastradas = list(
            MetaComissaoLoja.objects.filter(loja=self.loja)
            .order_by("valor_meta")
            .values_list("valor_meta", "percentual_comissao")
        )
        self.assertEqual(len(cadastradas), 4)
        self.assertEqual(cadastradas[-1], (Decimal("150000.00"), Decimal("8.00")))

    def test_nao_permite_duas_faixas_com_mesmo_valor_meta_na_mesma_loja(self):
        MetaComissaoLoja.objects.create(
            loja=self.loja,
            valor_meta=Decimal("50000.00"),
            percentual_comissao=Decimal("1.50"),
        )
        duplicada = MetaComissaoLoja(
            loja=self.loja,
            valor_meta=Decimal("50000.00"),
            percentual_comissao=Decimal("2.00"),
        )
        with self.assertRaises(ValidationError):
            duplicada.full_clean()

    def test_valores_de_meta_percentual_e_minimo_nao_podem_ser_negativos(self):
        cfg = ConfiguracaoComissaoMatriz(
            matriz=self.matriz,
            exigir_minimo_individual=True,
            minimo_vendas_vendedor=Decimal("-1.00"),
        )
        with self.assertRaises(ValidationError):
            cfg.full_clean()

        meta = MetaComissaoLoja(
            loja=self.loja,
            valor_meta=Decimal("-1.00"),
            percentual_comissao=Decimal("-0.01"),
        )
        with self.assertRaises(ValidationError):
            meta.full_clean()