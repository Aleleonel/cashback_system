from decimal import Decimal
from django.core.exceptions import ValidationError
from django.test import TestCase
from atacado.fiscal_contract import configurar_emissao_pedido_atacado
from atacado.models import (
    PedidoAtacado, OrcamentoAtacado, TipoEmissaoPedidoAtacado,
    ModeloFiscalPedidoAtacado, StatusOrcamentoAtacado,
)
from clientes.models import Cliente
from empresas.models import Loja, Matriz

class F32KContratoFiscalAtacadoTests(TestCase):
    def setUp(self):
        self.matriz=Matriz.objects.create(nome="Matriz F32K3")
        self.loja=Loja.objects.create(matriz=self.matriz,nome="Loja F32K3")
        self.cliente=Cliente.objects.create(matriz=self.matriz,loja_cadastro=self.loja,nome="Cliente F32K3")
    def pedido(self, loja=True):
        loja_obj=self.loja if loja else None
        o=OrcamentoAtacado.objects.create(
            matriz=self.matriz,loja=loja_obj,cliente=self.cliente,
            status=StatusOrcamentoAtacado.APROVADO,
            subtotal_produtos=Decimal("100"),total=Decimal("100"),
        )
        return PedidoAtacado.objects.create(
            orcamento_origem=o,matriz=self.matriz,loja=loja_obj,cliente=self.cliente,
            subtotal_produtos=Decimal("100"),desconto_atacado=Decimal("0"),
            ajustes_negociados=Decimal("0"),frete=Decimal("0"),total=Decimal("100"),
            percentual_desconto_snapshot=Decimal("0"),
            produto_promocional_conta_para_faixa_snapshot=False,
        )
    def test_default_e_nao_fiscal_sem_modelo(self):
        p=self.pedido()
        self.assertEqual(p.tipo_emissao,TipoEmissaoPedidoAtacado.NAO_FISCAL)
        self.assertEqual(p.modelo_fiscal,"")
        self.assertEqual(p.uf_destino_fiscal,"")
        self.assertIsNone(p.fiscal_solicitado_em)
    def test_fiscal_define_nfe55_uf_e_timestamp(self):
        p=configurar_emissao_pedido_atacado(pedido=self.pedido(),tipo_emissao=TipoEmissaoPedidoAtacado.FISCAL,uf_destino="sp")
        self.assertEqual(p.modelo_fiscal,ModeloFiscalPedidoAtacado.NFE)
        self.assertEqual(p.uf_destino_fiscal,"SP")
        self.assertIsNotNone(p.fiscal_solicitado_em)
    def test_fiscal_exige_loja_emissora(self):
        with self.assertRaises(ValidationError):
            configurar_emissao_pedido_atacado(pedido=self.pedido(loja=False),tipo_emissao=TipoEmissaoPedidoAtacado.FISCAL,uf_destino="SP")
    def test_fiscal_exige_uf_destino(self):
        with self.assertRaises(ValidationError):
            configurar_emissao_pedido_atacado(pedido=self.pedido(),tipo_emissao=TipoEmissaoPedidoAtacado.FISCAL,uf_destino="")
    def test_tipo_invalido_rejeitado(self):
        with self.assertRaises(ValidationError):
            configurar_emissao_pedido_atacado(pedido=self.pedido(),tipo_emissao="x",uf_destino="SP")
    def test_reverter_para_nao_fiscal_limpa_metadados(self):
        p=self.pedido()
        configurar_emissao_pedido_atacado(pedido=p,tipo_emissao=TipoEmissaoPedidoAtacado.FISCAL,uf_destino="SP")
        configurar_emissao_pedido_atacado(pedido=p,tipo_emissao=TipoEmissaoPedidoAtacado.NAO_FISCAL)
        p.refresh_from_db()
        self.assertEqual(p.modelo_fiscal,"");self.assertEqual(p.uf_destino_fiscal,"");self.assertIsNone(p.fiscal_solicitado_em)
