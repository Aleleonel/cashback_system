from dataclasses import FrozenInstanceError
from datetime import date

from django.core.exceptions import ValidationError
from django.test import TestCase

from empresas.models import Loja, Matriz
from fiscal.domain import ContextoSelecaoFiscal
from fiscal.models_configuracao_fiscal import ConfiguracaoFiscalMatriz
from fiscal.models_regra_fiscal import RegraFiscal
from fiscal.services_contexto_tributario import (
    construir_contexto_tributario,
)
from produtos.models import Produto
from produtos.models.unidades_medida import UnidadeMedida


class ContextoTributarioTests(TestCase):
    def setUp(self):
        self.matriz = Matriz.objects.create(
            nome="Matriz Contexto",
            cnpj="11111111000191",
        )
        self.loja = Loja.objects.create(
            matriz=self.matriz,
            nome="Loja Contexto",
            cnpj="11111111000272",
        )
        self.unidade = UnidadeMedida.objects.create(
            matriz=self.matriz,
            sigla="UN",
            descricao="Unidade",
        )
        self.configuracao = ConfiguracaoFiscalMatriz.objects.create(
            matriz=self.matriz,
            regime_tributario=RegraFiscal.REGIME_NORMAL,
            uf_origem="SP",
            contribuinte_icms=True,
            consumidor_final_padrao=True,
            ativa=True,
        )

    def construir(self, **extras):
        dados = {
            "matriz": self.matriz,
            "loja": self.loja,
            "uf_destino": "SP",
        }
        dados.update(extras)
        return construir_contexto_tributario(**dados)

    def test_retorna_contexto_selecao_fiscal(self):
        contexto = self.construir()

        self.assertIsInstance(contexto, ContextoSelecaoFiscal)
        self.assertEqual(
            contexto.regime_tributario,
            RegraFiscal.REGIME_NORMAL,
        )
        self.assertEqual(contexto.uf_origem, "SP")
        self.assertEqual(contexto.uf_destino, "SP")

    def test_utiliza_data_informada(self):
        data_operacao = date(2026, 8, 6)

        contexto = self.construir(
            data_operacao=data_operacao,
        )

        self.assertEqual(contexto.data_operacao, data_operacao)

    def test_utiliza_data_atual_quando_ausente(self):
        contexto = self.construir()

        self.assertEqual(contexto.data_operacao, date.today())

    def test_exige_matriz(self):
        with self.assertRaises(ValidationError) as erro:
            construir_contexto_tributario(
                matriz=None,
                uf_destino="SP",
            )

        self.assertIn("matriz", erro.exception.message_dict)

    def test_exige_configuracao_fiscal_ativa(self):
        self.configuracao.ativa = False
        self.configuracao.save()

        with self.assertRaises(ValidationError) as erro:
            self.construir()

        self.assertIn(
            "configuracao_fiscal",
            erro.exception.message_dict,
        )

    def test_rejeita_loja_de_outra_matriz(self):
        outra_matriz = Matriz.objects.create(
            nome="Outra Matriz",
            cnpj="22222222000191",
        )
        outra_loja = Loja.objects.create(
            matriz=outra_matriz,
            nome="Outra Loja",
            cnpj="22222222000272",
        )

        with self.assertRaises(ValidationError) as erro:
            self.construir(loja=outra_loja)

        self.assertIn("loja", erro.exception.message_dict)

    def test_funciona_sem_loja(self):
        contexto = self.construir(loja=None)

        self.assertIsNone(contexto.loja)

    def test_normaliza_uf_destino(self):
        contexto = self.construir(uf_destino=" rj ")

        self.assertEqual(contexto.uf_destino, "RJ")

    def test_rejeita_uf_destino_invalida(self):
        with self.assertRaises(ValidationError) as erro:
            self.construir(uf_destino="XX")

        self.assertIn("uf_destino", erro.exception.message_dict)

    def test_nao_inventa_uf_destino(self):
        with self.assertRaises(ValidationError) as erro:
            self.construir(uf_destino="")

        self.assertIn("uf_destino", erro.exception.message_dict)

    def test_valor_explicito_false_prevalece(self):
        contexto = self.construir(
            contribuinte_icms=False,
            consumidor_final=False,
        )

        self.assertFalse(contexto.contribuinte_icms)
        self.assertFalse(contexto.consumidor_final)

    def test_configuracao_fornece_fallback_booleano(self):
        contexto = self.construir(
            contribuinte_icms=None,
            consumidor_final=None,
        )

        self.assertTrue(contexto.contribuinte_icms)
        self.assertTrue(contexto.consumidor_final)

    def test_utiliza_ncm_e_cest_do_produto(self):
        produto = Produto.objects.create(
            matriz=self.matriz,
            unidade_medida=self.unidade,
            codigo_interno="CTX-001",
            nome="Produto Contexto",
            sku="CTX-001",
            preco_venda="10.00",
            ncm="21069090",
        )

        contexto = self.construir(produto=produto)

        self.assertEqual(contexto.ncm, "21069090")
        self.assertEqual(contexto.cest, produto.cest)

    def test_nao_altera_produto(self):
        produto = Produto.objects.create(
            matriz=self.matriz,
            unidade_medida=self.unidade,
            codigo_interno="CTX-002",
            nome="Produto Imutavel",
            sku="CTX-002",
            preco_venda="10.00",
            ncm="21069090",
        )

        self.construir(produto=produto)

        produto.refresh_from_db()
        self.assertEqual(produto.ncm, "21069090")

    def test_contexto_e_imutavel(self):
        contexto = self.construir()

        with self.assertRaises(FrozenInstanceError):
            contexto.uf_destino = "RJ"
