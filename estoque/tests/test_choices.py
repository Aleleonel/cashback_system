from django.test import SimpleTestCase

from estoque.choices import (
    NATUREZA_POR_TIPO_MOVIMENTACAO,
    NaturezaMovimentacao,
    OrigemMovimentacao,
    TipoMovimentacao,
    get_natureza_tipo_movimentacao,
    tipo_movimentacao_compativel_com_natureza,
)


class ChoicesEstoqueTestCase(SimpleTestCase):
    def test_naturezas_disponiveis(self):
        self.assertEqual(
            set(NaturezaMovimentacao.values),
            {
                'entrada',
                'saida',
            }
        )

    def test_origens_estruturais_disponiveis(self):
        self.assertEqual(
            set(OrigemMovimentacao.values),
            {
                'manual',
                'inventario',
                'transferencia',
                'compra',
                'venda',
                'fiscal',
                'sistema',
            }
        )

    def test_todos_os_tipos_possuem_natureza_definida(self):
        self.assertEqual(
            set(NATUREZA_POR_TIPO_MOVIMENTACAO.keys()),
            set(TipoMovimentacao.values)
        )

    def test_tipos_de_entrada(self):
        tipos_entrada = {
            TipoMovimentacao.SALDO_INICIAL,
            TipoMovimentacao.ENTRADA_MANUAL,
            TipoMovimentacao.AJUSTE_POSITIVO,
            TipoMovimentacao.TRANSFERENCIA_ENTRADA,
            TipoMovimentacao.INVENTARIO_ENTRADA,
            TipoMovimentacao.REVERSAO_ENTRADA,
            TipoMovimentacao.COMPRA,
            TipoMovimentacao.DEVOLUCAO_VENDA,
        }

        for tipo in tipos_entrada:
            with self.subTest(tipo=tipo):
                self.assertEqual(
                    get_natureza_tipo_movimentacao(tipo),
                    NaturezaMovimentacao.ENTRADA
                )

    def test_tipos_de_saida(self):
        tipos_saida = {
            TipoMovimentacao.SAIDA_MANUAL,
            TipoMovimentacao.AJUSTE_NEGATIVO,
            TipoMovimentacao.TRANSFERENCIA_SAIDA,
            TipoMovimentacao.INVENTARIO_SAIDA,
            TipoMovimentacao.REVERSAO_SAIDA,
            TipoMovimentacao.DEVOLUCAO_COMPRA,
            TipoMovimentacao.VENDA,
        }

        for tipo in tipos_saida:
            with self.subTest(tipo=tipo):
                self.assertEqual(
                    get_natureza_tipo_movimentacao(tipo),
                    NaturezaMovimentacao.SAIDA
                )

    def test_compatibilidade_tipo_natureza_valida(self):
        self.assertTrue(
            tipo_movimentacao_compativel_com_natureza(
                tipo=TipoMovimentacao.COMPRA,
                natureza=NaturezaMovimentacao.ENTRADA,
            )
        )

        self.assertTrue(
            tipo_movimentacao_compativel_com_natureza(
                tipo=TipoMovimentacao.VENDA,
                natureza=NaturezaMovimentacao.SAIDA,
            )
        )

    def test_compatibilidade_tipo_natureza_invalida(self):
        self.assertFalse(
            tipo_movimentacao_compativel_com_natureza(
                tipo=TipoMovimentacao.COMPRA,
                natureza=NaturezaMovimentacao.SAIDA,
            )
        )

        self.assertFalse(
            tipo_movimentacao_compativel_com_natureza(
                tipo='tipo_inexistente',
                natureza=NaturezaMovimentacao.ENTRADA,
            )
        )

    def test_fiscal_e_origem_e_nao_tipo_fisico(self):
        self.assertIn(
            OrigemMovimentacao.FISCAL,
            OrigemMovimentacao.values
        )

        tipos_fiscais_redundantes = {
            'fiscal_entrada',
            'fiscal_saida',
            'cancelamento_fiscal_entrada',
            'cancelamento_fiscal_saida',
        }

        self.assertTrue(
            tipos_fiscais_redundantes.isdisjoint(
                set(TipoMovimentacao.values)
            )
        )
