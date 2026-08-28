from decimal import Decimal
from types import SimpleNamespace
from django.test import SimpleTestCase
from fiscal.services_xml_nfce import NFE_NAMESPACE, adicionar_total_nfce, criar_envelope_nfce

NS = {"nfe": NFE_NAMESPACE}

def _item(valor_produtos="100.00", base_icms="100.00", valor_icms="18.00"):
    return SimpleNamespace(
        valor_produtos=Decimal(valor_produtos),
        base_icms=Decimal(base_icms),
        valor_icms=Decimal(valor_icms),
        desconto=Decimal("0.00"), frete=Decimal("0.00"),
        seguro=Decimal("0.00"), outras_despesas=Decimal("0.00"),
    )

def _total(itens):
    nfe = criar_envelope_nfce("35" + "1" * 42)
    inf_nfe = nfe.find(f"{{{NFE_NAMESPACE}}}infNFe")
    adicionar_total_nfce(inf_nfe, itens=itens)
    return inf_nfe.find("nfe:total/nfe:ICMSTot", NS)

class TotalizacaoICMS00195F2A4C2Tests(SimpleTestCase):
    def test_um_item(self):
        total = _total([_item()])
        self.assertEqual(total.findtext("nfe:vBC", namespaces=NS), "100.00")
        self.assertEqual(total.findtext("nfe:vICMS", namespaces=NS), "18.00")
        self.assertEqual(total.findtext("nfe:vICMSDeson", namespaces=NS), "0.00")

    def test_multiplos_itens(self):
        total = _total([_item("100.00","90.00","16.20"), _item("50.00","50.00","9.00")])
        self.assertEqual(total.findtext("nfe:vBC", namespaces=NS), "140.00")
        self.assertEqual(total.findtext("nfe:vICMS", namespaces=NS), "25.20")
        self.assertEqual(total.findtext("nfe:vProd", namespaces=NS), "150.00")
        self.assertEqual(total.findtext("nfe:vNF", namespaces=NS), "150.00")

    def test_nao_recalcula_por_aliquota(self):
        item = _item("100.00","100.00","7.77")
        item.aliquota_icms = Decimal("18.0000")
        total = _total([item])
        self.assertEqual(total.findtext("nfe:vICMS", namespaces=NS), "7.77")

    def test_soma_decimal_formata_no_final(self):
        total = _total([_item("1.005","1.005","0.105"), _item("2.005","2.005","0.205")])
        self.assertEqual(total.findtext("nfe:vBC", namespaces=NS), "3.01")
        self.assertEqual(total.findtext("nfe:vICMS", namespaces=NS), "0.31")

    def test_item_legado_sem_icms_totaliza_zero(self):
        item = SimpleNamespace(
            valor_produtos=Decimal("10.00"), desconto=Decimal("0.00"),
            frete=Decimal("0.00"), seguro=Decimal("0.00"),
            outras_despesas=Decimal("0.00"),
        )
        total = _total([item])
        self.assertEqual(total.findtext("nfe:vBC", namespaces=NS), "0.00")
        self.assertEqual(total.findtext("nfe:vICMS", namespaces=NS), "0.00")
