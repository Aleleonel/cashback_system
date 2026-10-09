from pathlib import Path
from django.test import SimpleTestCase

class HistoricoVendasEscopoLojaContratoTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.views = Path("pdv/views.py").read_text(encoding="utf-8")
        cls.template = Path("pdv/templates/pdv/historico_vendas.html").read_text(encoding="utf-8")
        ini = cls.views.index("def historico_vendas(request):")
        fim = cls.views.index("def detalhe_venda", ini)
        cls.trecho = cls.views[ini:fim]

    def test_backend_distingue_operador_de_administrativo(self):
        self.assertIn("PERFIL_OPERADOR", self.trecho)

    def test_operador_usa_loja_operacional_da_sessao(self):
        self.assertIn("loja_operacional_id", self.trecho)

    def test_operador_tem_guarda_contra_filtro_loja_arbitrario(self):
        self.assertTrue(
            "pode_filtrar_loja" in self.trecho or "usuario_operacional" in self.trecho,
            "Historico ainda nao possui guarda explicita para impedir filtro Loja pelo operador.",
        )

    def test_template_condiciona_filtro_loja_por_perfil(self):
        self.assertTrue(
            "pode_filtrar_loja" in self.template or "usuario_operacional" in self.template,
            "Filtro Loja ainda e exibido sem condicao de perfil.",
        )