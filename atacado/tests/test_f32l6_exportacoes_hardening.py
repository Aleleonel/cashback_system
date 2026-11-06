from io import BytesIO
from decimal import Decimal
from django.test import TestCase
from openpyxl import load_workbook
from empresas.models import Matriz, Loja
from clientes.models import Cliente
from produtos.models import Produto
from atacado.models import OrcamentoAtacado, PedidoAtacado
from atacado.exports import exportar_orcamento_pdf, exportar_orcamento_xlsx, exportar_pedido_pdf, exportar_pedido_xlsx

class F32L6ExportacoesHardeningTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.matriz=Matriz.objects.create(nome="Matriz F32L6")
        cls.loja=Loja.objects.create(matriz=cls.matriz,nome="Loja F32L6")
        cls.cliente=Cliente.objects.create(matriz=cls.matriz,loja_cadastro=cls.loja,nome="Cliente Áção F32L6")
        UnidadeMedida=Produto._meta.get_field("unidade_medida").remote_field.model
        cls.unidade=UnidadeMedida.objects.create(matriz=cls.matriz,sigla="UN",descricao="UNIDADE")
        cls.produto=Produto.objects.create(matriz=cls.matriz,nome="Produto F32L6",codigo_interno="F32L6-PROD",unidade_medida=cls.unidade,preco_venda=Decimal("100.00"))
        cls.orc=OrcamentoAtacado.objects.create(
            matriz=cls.matriz,loja=cls.loja,cliente=cls.cliente,numero=654,
            subtotal_produtos=Decimal("0.00"),desconto_atacado=Decimal("0.00"),
            ajustes_negociados=Decimal("0.00"),frete=Decimal("12.34"),total=Decimal("56.78"),
            observacoes="Áção çãõ – teste Unicode",
        )
        cls.ped=PedidoAtacado.objects.create(
            orcamento_origem=cls.orc,matriz=cls.matriz,loja=cls.loja,cliente=cls.cliente,
            subtotal_produtos=Decimal("0.00"),desconto_atacado=Decimal("0.00"),
            ajustes_negociados=Decimal("0.00"),frete=Decimal("12.34"),total=Decimal("56.78"),
            observacoes_snapshot="Áção çãõ – pedido Unicode",
        )
    def values(self,data):
        ws=load_workbook(BytesIO(data),data_only=True).active
        return [c.value for row in ws.iter_rows() for c in row if c.value is not None]
    def test_orcamento_sem_itens_unicode_decimal(self):
        self.assertEqual(self.orc.itens.count(),0)
        self.assertTrue(exportar_orcamento_pdf(self.orc).startswith(b"%PDF"))
        v=self.values(exportar_orcamento_xlsx(self.orc))
        self.assertIn("Áção çãõ – teste Unicode",v);self.assertIn(12.34,v);self.assertIn(56.78,v)
    def test_pedido_sem_itens_unicode_decimal(self):
        self.assertEqual(self.ped.itens.count(),0)
        self.assertTrue(exportar_pedido_pdf(self.ped).startswith(b"%PDF"))
        v=self.values(exportar_pedido_xlsx(self.ped))
        self.assertIn("Áção çãõ – pedido Unicode",v);self.assertIn(12.34,v);self.assertIn(56.78,v)
    def test_vendedor_nulo(self):
        self.assertIsNone(self.orc.vendedor)
        self.assertIn("-",self.values(exportar_orcamento_xlsx(self.orc)))
    def test_exportacao_nao_muta_campos_persistidos(self):
        antes={f.attname:getattr(self.orc,f.attname) for f in self.orc._meta.concrete_fields}
        exportar_orcamento_pdf(self.orc);exportar_orcamento_xlsx(self.orc)
        self.orc.refresh_from_db()
        depois={f.attname:getattr(self.orc,f.attname) for f in self.orc._meta.concrete_fields}
        self.assertEqual(antes,depois)
