from pathlib import Path
from django.test import SimpleTestCase
class F2EA15ColunaLojaAdminTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.table=Path("estoque/templates/estoque/movimentacoes/_tabela_conteudo.html").read_text(encoding="utf-8")
        cls.view=Path("estoque/views/movimentacoes.py").read_text(encoding="utf-8")
    def test_coluna_loja_condicional_admin(self):
        self.assertIn("{% if pode_filtrar_loja %}<th scope=\"col\">Loja</th>{% endif %}",self.table)
        self.assertIn("{% if pode_filtrar_loja %}<td>{{ movimentacao.loja.nome }}</td>{% endif %}",self.table)
    def test_estado_vazio_ajusta_colspan(self):
        self.assertIn("colunas=colunas_tabela",self.table)
        self.assertIn("'colunas_tabela': 6 if pode_filtrar_loja else 5",self.view)