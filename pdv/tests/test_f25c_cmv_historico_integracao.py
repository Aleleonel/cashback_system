from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from empresas.models import Loja, Matriz
from pdv.models import ItemVenda, Venda
from pdv.services.vendas.finalizacao import _congelar_custo_itens
from produtos.models import Produto, UnidadeMedida


class F25CCMVHistoricoIntegracaoTests(TestCase):
    def setUp(self):
        self.matriz = Matriz.objects.create(nome="Matriz F25C8B")
        self.loja = Loja.objects.create(matriz=self.matriz, nome="Loja F25C8B")
        self.unidade = UnidadeMedida.objects.create(matriz=self.matriz, sigla="UN", descricao="Unidade F25C8B")
        self.usuario = get_user_model().objects.create_user(
            username="f25c8b",
            password="teste",
        )

    def _produto(self, *, nome, custo):
        seq = Produto.objects.filter(matriz=self.matriz).count() + 1
        return Produto.objects.create(
            matriz=self.matriz,
            unidade_medida=self.unidade,
            sku=f"F25C8B-{seq}",
            codigo_interno=f"F25C8B-{seq}",
            gtin="",
            ncm="",
            nome=nome,
            descricao="",
            custo_base=Decimal(custo),
            preco_venda=Decimal("100.00"),
        )

    def _venda(self):
        return Venda.objects.create(
            matriz=self.matriz,
            loja=self.loja,
            operador=self.usuario,
            observacao="F25C integracao CMV",
        )

    def _item(self, *, venda, produto, sequencia, quantidade="1.000"):
        return ItemVenda.objects.create(
            venda=venda,
            produto=produto,
            sequencia=sequencia,
            quantidade=Decimal(quantidade),
            preco_unitario=Decimal("100.00"),
            subtotal=Decimal("100.00"),
            total=Decimal("100.00"),
            observacao="",
            motivo_cancelamento="",
        )

    def test_copia_custo_base_vigente(self):
        produto = self._produto(nome="Produto custo", custo="53.13")
        venda = self._venda()
        item = self._item(venda=venda, produto=produto, sequencia=1)

        _congelar_custo_itens(venda=venda)

        item.refresh_from_db()
        self.assertEqual(item.custo_unitario_snapshot, Decimal("53.13"))

    def test_custo_zero_e_valido(self):
        produto = self._produto(nome="Produto zero", custo="0.00")
        venda = self._venda()
        item = self._item(venda=venda, produto=produto, sequencia=1)

        _congelar_custo_itens(venda=venda)

        item.refresh_from_db()
        self.assertEqual(item.custo_unitario_snapshot, Decimal("0.00"))

    def test_processa_multiplos_itens(self):
        p1 = self._produto(nome="Produto 1", custo="10.00")
        p2 = self._produto(nome="Produto 2", custo="20.00")
        venda = self._venda()
        i1 = self._item(venda=venda, produto=p1, sequencia=1)
        i2 = self._item(venda=venda, produto=p2, sequencia=2)

        _congelar_custo_itens(venda=venda)

        i1.refresh_from_db()
        i2.refresh_from_db()
        self.assertEqual(i1.custo_unitario_snapshot, Decimal("10.00"))
        self.assertEqual(i2.custo_unitario_snapshot, Decimal("20.00"))
