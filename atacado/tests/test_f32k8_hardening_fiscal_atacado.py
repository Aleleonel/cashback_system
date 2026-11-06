from decimal import Decimal
from types import SimpleNamespace

from django.core.exceptions import ValidationError
from django.test import TestCase

from atacado.fiscal_nfe55 import preparar_dados_nfe55_atacado


class F32K8HardeningFiscalAtacadoTests(TestCase):
    def pedido(self, **kw):
        data=dict(pk=1, matriz_id=1, loja_id=2, cliente_id=3, tipo_emissao="fiscal",
                  modelo_fiscal="55", uf_destino_fiscal="SP", frete=Decimal("10.00"),
                  subtotal_produtos=Decimal("100.00"), desconto_atacado=Decimal("0.00"),
                  ajustes_negociados=Decimal("0.00"), total=Decimal("110.00"))
        data.update(kw)
        return SimpleNamespace(**data)

    def test_rejeita_uf_inexistente_com_duas_letras(self):
        with self.assertRaises(ValidationError):
            preparar_dados_nfe55_atacado(self.pedido(uf_destino_fiscal="XX"))

    def test_normaliza_uf_valida(self):
        dados=preparar_dados_nfe55_atacado(self.pedido(uf_destino_fiscal=" sp "))
        self.assertEqual("SP", dados.uf_destino)

    def test_rejeita_nfce_65(self):
        with self.assertRaises(ValidationError):
            preparar_dados_nfe55_atacado(self.pedido(modelo_fiscal="65"))

    def test_preparacao_nao_cria_documento_fiscal(self):
        from fiscal.models_documento_fiscal import DocumentoFiscal
        before = DocumentoFiscal.objects.count()
        dados = preparar_dados_nfe55_atacado(self.pedido())
        self.assertEqual("55", dados.modelo)
        self.assertEqual(before, DocumentoFiscal.objects.count())
