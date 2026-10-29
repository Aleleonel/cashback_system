from pathlib import Path
from django.test import SimpleTestCase
from django.urls import reverse
from configuracoes.catalogo import GRUPOS_CONFIGURACAO

ROOT = Path(__file__).resolve().parents[1]

class F27G2ClientesCashbackVouchersRedTests(SimpleTestCase):
    def _grupo(self, codigo):
        return next((g for g in GRUPOS_CONFIGURACAO if g.codigo == codigo), None)

    def test_hub_possui_card_vouchers_disponivel(self):
        grupo = self._grupo("vouchers")
        self.assertIsNotNone(grupo, "Hub deve possuir card dedicado de Vouchers.")
        self.assertTrue(grupo.disponivel)
        self.assertTrue(grupo.url_name)

    def test_card_vouchers_aponta_para_integracao_da_central(self):
        grupo = self._grupo("vouchers")
        self.assertEqual(grupo.url_name, "configuracoes:vouchers")
        self.assertEqual(reverse("configuracoes:vouchers"), "/configuracoes/vouchers/")

    def test_clientes_cashback_nao_tem_cta_solto_fora_da_grade(self):
        html = (ROOT/"configuracoes"/"templates"/"configuracoes"/"clientes_cashback.html").read_text(encoding="utf-8")
        self.assertNotIn(">Configurar Cashback</a>", html)
        self.assertIn("Configura", html)
        self.assertIn("cashback", html.lower())

    def test_clientes_cashback_mantem_fluxo_oficial_cashback(self):
        html = (ROOT/"configuracoes"/"templates"/"configuracoes"/"clientes_cashback.html").read_text(encoding="utf-8")
        self.assertIn("empresa:configurar_cashback", html)

    def test_vouchers_reutiliza_fluxos_oficiais_existentes(self):
        html = (ROOT/"configuracoes"/"templates"/"configuracoes"/"vouchers.html").read_text(encoding="utf-8")
        self.assertIn("vouchers:lista_vouchers", html)
        self.assertIn("vouchers:criar_voucher", html)
        self.assertNotIn("Configurações futuras de vouchers", html)

    def test_vouchers_nao_duplica_regra_comercial_global(self):
        html = (ROOT/"configuracoes"/"templates"/"configuracoes"/"vouchers.html").read_text(encoding="utf-8")
        self.assertNotIn('name="voucher_ativo"', html)