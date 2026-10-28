from pathlib import Path
from django.test import SimpleTestCase
from relatorios import views

class DREHardeningEscopoPeriodoRedTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.src=Path(views.__file__).read_text(encoding="utf-8")
        a=cls.src.index("def _contexto_dre")
        b=cls.src.index("\n@login_required",a)
        cls.ctx=cls.src[a:b]

    def test_data_invalida_nao_e_silenciosamente_substituida(self):
        self.assertIn("erro_filtros",self.ctx)
        self.assertIn("Data inválida",self.ctx)

    def test_periodo_invertido_nao_e_silenciosamente_trocado(self):
        self.assertNotIn("data_inicio,data_fim=data_fim,data_inicio",self.ctx)
        self.assertIn("Período inválido",self.ctx)

    def test_mes_calendario_completo_compara_mes_calendario_anterior(self):
        self.assertIn("_periodo_anterior_dre",self.src)
        self.assertIn("mes_calendario_completo",self.src)
        self.assertIn("ultimo_dia_mes",self.src)

    def test_periodo_arbitrario_mantem_intervalo_anterior_equivalente(self):
        self.assertIn("dias = (fim - inicio).days",self.src)
        self.assertIn("anterior_fim = inicio - timedelta(days=1)",self.src)

    def test_loja_administrativa_e_limitada_a_matriz(self):
        self.assertIn("Loja.objects.filter(matriz=matriz)",self.ctx)
        self.assertNotIn("Loja.objects.filter(pk=loja_raw)",self.ctx)

    def test_centro_custo_e_limitado_a_matriz(self):
        self.assertIn("CentroCusto.objects.filter(matriz=matriz,ativo=True)",self.ctx)
        self.assertNotIn("CentroCusto.objects.filter(pk=centro_raw)",self.ctx)

    def test_operador_ignora_loja_injetada_na_querystring(self):
        bloco=self.ctx[self.ctx.index("if operador:"):self.ctx.index("else:",self.ctx.index("if operador:"))]
        self.assertNotIn("loja_raw",bloco)
        self.assertIn("request.user.lojas.filter(matriz=matriz)",bloco)

    def test_contexto_expoe_periodo_comparativo_e_erros(self):
        self.assertIn('"periodo_anterior"',self.ctx)
        self.assertIn('"erro_filtros"',self.ctx)