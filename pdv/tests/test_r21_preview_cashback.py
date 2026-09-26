from pathlib import Path
from django.test import SimpleTestCase, TestCase

ROOT = Path(__file__).resolve().parents[2]
FECHAMENTO = (ROOT / "pdv/services/vendas/fechamento.py").read_text(encoding="utf-8")
JS = (ROOT / "pdv/static/pdv/js/frente_caixa.js").read_text(encoding="utf-8")

class R21PreviewCashbackContratoTests(TestCase):
    def test_modal_expoe_base_e_cashback_previsto(self):
        html = (Path(__file__).resolve().parents[1] / "templates" / "pdv" / "inicio.html").read_text(encoding="utf-8")
        self.assertIn('id="pdv-fechamento-base-cashback"', html)
        self.assertIn('id="pdv-fechamento-cashback-previsto"', html)
        self.assertIn("Base elegível para cashback", html)
        self.assertIn("Cashback previsto", html)

    def test_formas_pagamento_expoem_gera_cashback_ao_frontend(self):
        inicio = FECHAMENTO.index("def serializar_formas_pagamento")
        fim = FECHAMENTO.index("\n\ndef ", inicio + 1)
        bloco = FECHAMENTO[inicio:fim]
        self.assertIn('"gera_cashback": forma.gera_cashback', bloco)

    def test_frontend_calcula_base_elegivel_das_linhas_de_pagamento(self):
        self.assertIn("gera_cashback", JS)
        self.assertIn("baseCashback", JS)
        self.assertIn("cashback_previsto", JS)
    def test_serializer_preview_expoe_id_e_gera_cashback_coerentes(self):
        """R21 L17: contrato do preview exige id + gera_cashback coerentes no payload."""
        from pdv.services.vendas.fechamento import serializar_formas_pagamento
        from empresas.models import Matriz
        from pdv.models import FormaPagamento

        matriz = Matriz.objects.create(nome="Matriz R21 L17D")
        FormaPagamento.objects.create(
            matriz=matriz,
            codigo="CREDIARIO",
            nome="Crediário",
            tipo="OUTRO",
            gera_cashback=False,
            gera_contas_receber=True,
            movimenta_caixa=False,
        )
        formas = serializar_formas_pagamento(matriz=matriz)
        pix = next((f for f in formas if f.get("nome") == "PIX"), None)
        crediario = next((f for f in formas if f.get("nome") == "Crediário"), None)
        self.assertIsNotNone(pix)
        self.assertIsNotNone(crediario)
        self.assertIsInstance(pix.get("id"), int)
        self.assertIsInstance(crediario.get("id"), int)
        self.assertIs(pix.get("gera_cashback"), True)
        self.assertIs(crediario.get("gera_cashback"), False)