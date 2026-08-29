from decimal import Decimal
from types import SimpleNamespace
from django.test import SimpleTestCase
from fiscal.services_xml_nfce import NFE_NAMESPACE, adicionar_total_nfce, criar_envelope_nfce
NS={"nfe":NFE_NAMESPACE}
def I(vp,pis,cof): return SimpleNamespace(valor_produtos=Decimal(vp),desconto=Decimal("0"),frete=Decimal("0"),seguro=Decimal("0"),outras_despesas=Decimal("0"),base_icms=Decimal("0"),valor_icms=Decimal("0"),valor_pis=Decimal(pis),valor_cofins=Decimal(cof))
def T(xs):
 n=criar_envelope_nfce("35"+"1"*42);i=n.find("{%s}infNFe"%NFE_NAMESPACE);adicionar_total_nfce(i,itens=xs);return i.find("nfe:total/nfe:ICMSTot",NS)
class B3(SimpleTestCase):
 def test_venda39(self):
  x=T([I("100","1.65","7.60"),I("50","0.83","3.80")]);self.assertEqual(x.findtext("nfe:vPIS",namespaces=NS),"2.48");self.assertEqual(x.findtext("nfe:vCOFINS",namespaces=NS),"11.40")
 def test_nao_recalcula(self):
  x=T([I("100","9.99","8.88")]);self.assertEqual(x.findtext("nfe:vPIS",namespaces=NS),"9.99");self.assertEqual(x.findtext("nfe:vCOFINS",namespaces=NS),"8.88")
