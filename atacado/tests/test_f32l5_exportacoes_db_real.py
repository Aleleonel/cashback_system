from io import BytesIO
from decimal import Decimal
from django.test import TestCase
from openpyxl import load_workbook

from empresas.models import Matriz, Loja
from clientes.models import Cliente
from produtos.models import Produto
from atacado.models import OrcamentoAtacado, ItemOrcamentoAtacado, PedidoAtacado, ItemPedidoAtacado
from atacado.exports import exportar_orcamento_pdf, exportar_orcamento_xlsx, exportar_pedido_pdf, exportar_pedido_xlsx


class F32L5ExportacoesDBRealTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Reutiliza factories mínimas tolerantes aos campos reais do projeto.
        cls.matriz=Matriz.objects.create(nome="Matriz F32L5")
        cls.loja=Loja.objects.create(matriz=cls.matriz,nome="Loja F32L5")
        cls.cliente=Cliente.objects.create(matriz=cls.matriz,loja_cadastro=cls.loja,nome="Cliente F32L5")
        unidade = Produto._meta.get_field("unidade_medida").remote_field.model.objects.filter(matriz=cls.matriz).first()
        if unidade is None:
            UnidadeMedida = Produto._meta.get_field("unidade_medida").remote_field.model
            unidade = UnidadeMedida.objects.create(matriz=cls.matriz, sigla="UN", descricao="UNIDADE")
        cls.produto=Produto.objects.create(matriz=cls.matriz,nome="Produto F32L5",codigo_interno="F32L5-PROD",unidade_medida=unidade,preco_venda=Decimal("100.00"))
        cls.orc=OrcamentoAtacado.objects.create(
            matriz=cls.matriz,loja=cls.loja,cliente=cls.cliente,numero=321,
            subtotal_produtos=Decimal("200.00"),desconto_atacado=Decimal("10.00"),
            ajustes_negociados=Decimal("-5.00"),frete=Decimal("20.00"),total=Decimal("205.00"),
            observacoes="Observacao F32L5",
        )
        cls.io=ItemOrcamentoAtacado.objects.create(
            orcamento=cls.orc,produto=cls.produto,quantidade=Decimal("2"),
            preco_unitario_original=Decimal("100"),preco_unitario_base=Decimal("100"),
            preco_unitario_final=Decimal("95"),percentual_desconto_atacado=Decimal("5"),
            desconto_atacado=Decimal("10"),ajuste_negociado=Decimal("-5"),
            produto_promocional=False,atacado_elegivel=True,conta_para_enquadramento=True,
            justificativa_negociacao="Acordo F32L5",
        )
        cls.ped=PedidoAtacado.objects.create(
            orcamento_origem=cls.orc,matriz=cls.matriz,loja=cls.loja,cliente=cls.cliente,
            subtotal_produtos=Decimal("200"),desconto_atacado=Decimal("10"),
            ajustes_negociados=Decimal("-5"),frete=Decimal("20"),total=Decimal("205"),
            observacoes_snapshot="Observacao Pedido F32L5",
        )
        cls.ip=ItemPedidoAtacado.objects.create(
            pedido=cls.ped,produto=cls.produto,quantidade=Decimal("2"),
            preco_unitario_original=Decimal("100"),preco_unitario_base=Decimal("100"),
            preco_unitario_final=Decimal("95"),percentual_desconto=Decimal("5"),
            desconto_atacado=Decimal("10"),ajuste_negociado=Decimal("-5"),
            produto_promocional_snapshot=False,atacado_elegivel_snapshot=True,
            conta_para_enquadramento_snapshot=True,justificativa_negociacao_snapshot="Acordo F32L5",
        )

    def _xlsx_values(self,data):
        ws=load_workbook(BytesIO(data),data_only=True).active
        return [c.value for row in ws.iter_rows() for c in row if c.value is not None]

    def test_orcamento_relacao_real_e_exports(self):
        self.assertEqual(1,self.orc.itens.count())
        pdf=exportar_orcamento_pdf(self.orc)
        self.assertTrue(pdf.startswith(b"%PDF"))
        v=self._xlsx_values(exportar_orcamento_xlsx(self.orc))
        for x in ("F32L5-PROD - Produto F32L5","Cliente F32L5 - ","Observacao F32L5","Acordo F32L5"):
            self.assertIn(x,v)
        self.assertIn(20,v);self.assertIn(205,v)

    def test_pedido_relacao_real_e_exports(self):
        self.assertEqual(1,self.ped.itens.count())
        pdf=exportar_pedido_pdf(self.ped)
        self.assertTrue(pdf.startswith(b"%PDF"))
        v=self._xlsx_values(exportar_pedido_xlsx(self.ped))
        for x in ("F32L5-PROD - Produto F32L5","Cliente F32L5 - ","Observacao Pedido F32L5","Acordo F32L5"):
            self.assertIn(x,v)
        self.assertIn(20,v);self.assertIn(205,v)
