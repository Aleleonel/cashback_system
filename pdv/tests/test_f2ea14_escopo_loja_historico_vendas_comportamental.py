from pathlib import Path
from django.test import SimpleTestCase

class HistoricoVendasEscopoLojaComportamentalTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        text = Path("pdv/views.py").read_text(encoding="utf-8")
        ini = text.index("def historico_vendas(request):")
        fim = text.index("def detalhe_venda", ini)
        cls.view = text[ini:fim]
        cls.template = Path("pdv/templates/pdv/historico_vendas.html").read_text(encoding="utf-8")

    def test_operacional_restringe_queryset_a_uma_unica_loja(self):
        self.assertIn('lojas = lojas_relacao.filter(pk=loja_operacional.pk)', self.view)
        self.assertIn('loja__in=lojas', self.view)

    def test_operacional_querystring_loja_nao_altera_queryset(self):
        self.assertIn('if pode_filtrar_loja and loja_id.isdigit():', self.view)
        self.assertIn('elif usuario_operacional:', self.view)
        self.assertIn('loja_id = ""', self.view)

    def test_administrativo_recebe_lojas_da_matriz(self):
        self.assertIn('lojas = lojas_relacao.model.objects.filter(', self.view)
        self.assertIn('matriz=matriz,', self.view)
        self.assertIn('pode_filtrar_loja = not usuario_operacional', self.view)

    def test_template_oculta_select_para_operacional(self):
        self.assertIn('{% if pode_filtrar_loja %}', self.template)
        self.assertIn('value="{{ loja_operacional.nome }}" disabled', self.template)

    def test_totais_e_paginacao_derivam_do_queryset_restrito(self):
        pos_scope=self.view.index('loja__in=lojas')
        pos_totais=self.view.index('totais = vendas.aggregate')
        pos_paginator=self.view.index('Paginator(vendas, 20)')
        self.assertLess(pos_scope,pos_totais)
        self.assertLess(pos_totais,pos_paginator)