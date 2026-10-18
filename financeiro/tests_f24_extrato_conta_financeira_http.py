from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from financeiro.models import ContaFinanceira, BaixaFinanceira

class F24ExtratoContaFinanceiraHTTPTest(TestCase):
    def test_rota_extrato_resolve(self):
        conta = ContaFinanceira(uuid="11111111-1111-1111-1111-111111111111")
        url = reverse("financeiro:conta_financeira_extrato", kwargs={"conta_uuid": conta.uuid})
        self.assertIn("/financeiro/contas-financeiras/", url)
        self.assertTrue(url.endswith("/extrato/"))

    def test_template_extrato_existe_e_expoe_campos_essenciais(self):
        from pathlib import Path
        p=Path(__file__).resolve().parent/"templates"/"financeiro"/"conta_financeira_extrato.html"
        html=p.read_text(encoding="utf-8")
        for texto in ("Extrato da Conta Financeira","Data","Tipo","Natureza","T&iacute;tulo","Forma","Loja","Valor"):
            self.assertIn(texto,html)
        self.assertIn("titulo_detalhe",html)

    def test_view_exige_permissao_visualizar(self):
        from pathlib import Path
        txt=(Path(__file__).resolve().parent/"views.py").read_text(encoding="utf-8")
        pos=txt.index("def conta_financeira_extrato(")
        trecho=txt[max(0,pos-180):pos]
        self.assertIn("PERMISSAO_FINANCEIRO_VISUALIZAR",trecho)

    def test_view_filtra_eventos_pela_conta(self):
        from pathlib import Path
        txt=(Path(__file__).resolve().parent/"views.py").read_text(encoding="utf-8")
        pos=txt.index("def _extrato_conta_contexto(")
        fim=txt.find("\ndef ",pos+4)
        trecho=txt[pos:fim if fim!=-1 else None]
        self.assertIn("filter(conta_financeira=conta)",trecho)
        self.assertIn('order_by("-data","-criado_em","-pk")',trecho.replace(" ",""))

    def test_view_bloqueia_conta_de_loja_nao_autorizada(self):
        from pathlib import Path
        txt=(Path(__file__).resolve().parent/"views.py").read_text(encoding="utf-8")
        pos=txt.index("def _extrato_conta_contexto(")
        trecho=txt[pos:pos+1600]
        self.assertIn("lojas.filter(pk=conta.loja_id).exists()",trecho)
        self.assertIn("raise Http404",trecho)