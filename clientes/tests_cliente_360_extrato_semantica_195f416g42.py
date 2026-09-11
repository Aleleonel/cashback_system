from unittest.mock import patch
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
from clientes.tests_cliente_360_ux_extratos_195f416g4 import Cliente360UXExtratosTests

class Cliente360ExtratoSemantica195F416G42Tests(Cliente360UXExtratosTests):
    def _dt(self, days):
        return timezone.make_aware(datetime(2026,9,10,12,0,0))+timedelta(days=days)

    @patch("vouchers.selectors.get_usos_voucher")
    @patch("clientes.views.get_movimentacoes_cliente")
    def test_unifica_cashback_voucher_ordena_desc(self,movs,usos):
        movs.return_value=[
          {"data":self._dt(-2),"tipo":"ENTRADA","titulo":"Cashback gerado","loja":self.loja,"entrada":Decimal("10"),"saida":Decimal("0")},
          {"data":self._dt(0),"tipo":"SAIDA","titulo":"Cashback utilizado","loja":self.loja,"entrada":Decimal("0"),"saida":Decimal("3")}]
        u=type("UsoFake",(),{})();u.criado_em=self._dt(-1);u.loja=self.loja;u.valor_desconto=Decimal("5")
        u.voucher=type("VoucherFake",(),{"codigo":"V10","nome":"Voucher 10"})();usos.return_value=[u]
        r=self.client.get(self.url,{"secao":"extrato"});itens=list(r.context["extrato_page"].object_list)
        self.assertEqual([i["tipo"] for i in itens],["SAIDA","VOUCHER","ENTRADA"])
        self.assertEqual(itens[1]["valor"],Decimal("5"))

    @patch("vouchers.selectors.get_usos_voucher")
    @patch("clientes.views.get_movimentacoes_cliente")
    def test_datas_inicio_fim_inclusivas(self,movs,usos):
        movs.return_value=[
          {"data":self._dt(-1),"tipo":"ENTRADA","titulo":"A","loja":self.loja,"entrada":Decimal("1"),"saida":Decimal("0")},
          {"data":self._dt(0),"tipo":"SAIDA","titulo":"B","loja":self.loja,"entrada":Decimal("0"),"saida":Decimal("2")},
          {"data":self._dt(1),"tipo":"ENTRADA","titulo":"C","loja":self.loja,"entrada":Decimal("3"),"saida":Decimal("0")}]
        usos.return_value=[]
        r=self.client.get(self.url,{"secao":"extrato","data_inicio":"2026-09-10","data_fim":"2026-09-10"})
        itens=list(r.context["extrato_page"].object_list);self.assertEqual(len(itens),1);self.assertEqual(itens[0]["titulo"],"B")

    @patch("vouchers.selectors.get_usos_voucher")
    @patch("clientes.views.get_movimentacoes_cliente")
    def test_paginacao_20_preserva_query(self,movs,usos):
        movs.return_value=[{"data":self._dt(-i),"tipo":"ENTRADA","titulo":f"M{i}","loja":self.loja,"entrada":Decimal("1"),"saida":Decimal("0")} for i in range(25)]
        usos.return_value=[]
        r=self.client.get(self.url,{"secao":"extrato","data_inicio":"2026-08-01"})
        self.assertEqual(len(r.context["extrato_page"].object_list),20);self.assertEqual(r.context["extrato_page"].paginator.num_pages,2)
        self.assertIn("secao=extrato",r.context["query_string_extrato"]);self.assertIn("data_inicio=2026-08-01",r.context["query_string_extrato"])

    @patch("vouchers.selectors.get_usos_voucher")
    @patch("clientes.views.get_movimentacoes_cliente")
    def test_fontes_recebem_matriz_cliente(self,movs,usos):
        movs.return_value=[];usos.return_value=[];self.client.get(self.url,{"secao":"extrato"})
        movs.assert_called_once_with(matriz=self.cliente.matriz,cliente=self.cliente)
        usos.assert_called_once_with(matriz=self.cliente.matriz,cliente=self.cliente)