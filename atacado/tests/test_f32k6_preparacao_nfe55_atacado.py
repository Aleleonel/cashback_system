from decimal import Decimal
from types import SimpleNamespace

from django.core.exceptions import ValidationError
from django.test import SimpleTestCase


class F32K6ContratoPreparacaoNFe55AtacadoTests(SimpleTestCase):
    def _pedido(self, **kw):
        data = dict(
            pk=10,
            matriz_id=1,
            loja_id=2,
            cliente_id=3,
            tipo_emissao="fiscal",
            modelo_fiscal="55",
            uf_destino_fiscal="SP",
            frete=Decimal("25.00"),
            subtotal_produtos=Decimal("100.00"),
            desconto_atacado=Decimal("10.00"),
            ajustes_negociados=Decimal("0.00"),
            total=Decimal("115.00"),
        )
        data.update(kw)
        return SimpleNamespace(**data)

    def test_api_publica_existe(self):
        from atacado.fiscal_nfe55 import preparar_dados_nfe55_atacado
        self.assertTrue(callable(preparar_dados_nfe55_atacado))

    def test_rejeita_pedido_nao_fiscal(self):
        from atacado.fiscal_nfe55 import preparar_dados_nfe55_atacado
        with self.assertRaises(ValidationError):
            preparar_dados_nfe55_atacado(
                self._pedido(tipo_emissao="nao_fiscal")
            )

    def test_exige_modelo_55(self):
        from atacado.fiscal_nfe55 import preparar_dados_nfe55_atacado
        with self.assertRaises(ValidationError):
            preparar_dados_nfe55_atacado(
                self._pedido(modelo_fiscal="65")
            )

    def test_exige_loja(self):
        from atacado.fiscal_nfe55 import preparar_dados_nfe55_atacado
        with self.assertRaises(ValidationError):
            preparar_dados_nfe55_atacado(
                self._pedido(loja_id=None)
            )

    def test_frete_permanece_separado_dos_produtos(self):
        from atacado.fiscal_nfe55 import preparar_dados_nfe55_atacado
        dados=preparar_dados_nfe55_atacado(self._pedido())
        self.assertEqual(Decimal("25.00"), dados.frete)
        self.assertEqual(Decimal("100.00"), dados.subtotal_produtos)
        self.assertEqual(Decimal("115.00"), dados.total)

    def test_contrato_declara_nfe55_sem_emitir_sefaz(self):
        from atacado.fiscal_nfe55 import preparar_dados_nfe55_atacado
        dados=preparar_dados_nfe55_atacado(self._pedido())
        self.assertEqual("55", dados.modelo)
        self.assertEqual("SP", dados.uf_destino)
        self.assertFalse(hasattr(dados, "protocolo_autorizacao"))
