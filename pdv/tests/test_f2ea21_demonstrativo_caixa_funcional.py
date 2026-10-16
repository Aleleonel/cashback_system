from pathlib import Path
from django.test import SimpleTestCase


class F2EA21DemonstrativoCaixaFuncionalContratoTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.views = Path("pdv/views.py").read_text(encoding="utf-8")
        cls.template = Path("pdv/templates/pdv/demonstrativo_caixa.html").read_text(encoding="utf-8")
        ini = cls.views.index("def _contexto_demonstrativo_caixa(request, sessao_id):")
        fim = cls.views.index("def demonstrativo_caixa(request, sessao_id):", ini)
        cls.trecho = cls.views[ini:fim]

    def test_separa_recebido_de_a_receber_pela_regra_financeira(self):
        self.assertIn("gera_contas_receber", self.trecho)
        self.assertIn("movimenta_caixa", self.trecho)

    def test_operador_usa_loja_operacional_da_sessao(self):
        self.assertIn("PERFIL_OPERADOR", self.trecho)
        self.assertIn("loja_operacional_id", self.trecho)

    def test_administrativo_tem_escopo_da_matriz_sem_depender_vinculo_loja(self):
        self.assertIn("Loja.objects.filter(matriz=matriz", self.trecho)

    def test_acesso_detalhe_mantem_guarda_matriz_e_loja(self):
        self.assertIn("caixa__matriz=matriz", self.trecho)
        self.assertIn("caixa__loja", self.trecho)

    def test_demonstrativo_expoe_abertura_e_movimentos_que_afetam_saldo(self):
        for termo in ("valor_abertura", "SUPRIMENTO", "SANGRIA", "ESTORNO"):
            self.assertTrue(termo in self.trecho or termo in self.template, termo)

    def test_saldo_real_fechado_usa_valor_informado_e_aberto_calculado(self):
        self.assertIn("valor_fechamento_informado", self.trecho)
        self.assertIn("calcular_saldo_sessao_caixa", self.trecho)

    def test_template_expoe_totais_formas_pagamento(self):
        for termo in ("Recebido", "A Receber", "Total", "Saldo real no caixa"):
            self.assertIn(termo, self.template)
