from pathlib import Path
from django.test import SimpleTestCase


class R18ImportacaoCsvContratoRedTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        base = Path(__file__).resolve().parent
        cls.views = (base / "views.py").read_text(encoding="utf-8")
        cls.urls = (base / "urls.py").read_text(encoding="utf-8")
        cls.template = (base / "templates" / "financeiro" / "titulos.html").read_text(encoding="utf-8")
        cls.importador_path = base / "importacao_csv.py"
        cls.importador = cls.importador_path.read_text(encoding="utf-8") if cls.importador_path.exists() else ""

    def test_rota_importacao_csv_existe(self):
        self.assertIn('name="titulos_importar_csv"', self.urls)

    def test_view_exige_permissao_lancar_despesa(self):
        inicio = self.views.index("def titulos_importar_csv")
        trecho = self.views[max(0, inicio - 350):inicio + 2600]
        self.assertIn("@login_required", trecho)
        self.assertIn("@require_permission(PERMISSAO_FINANCEIRO_LANCAR_DESPESA)", trecho)

    def test_view_revalida_matriz_e_escopo_no_backend(self):
        inicio = self.views.index("def titulos_importar_csv")
        trecho = self.views[inicio:inicio + 3000]
        self.assertIn("_matriz_usuario(request)", trecho)
        self.assertIn("_resolver_escopo(request, matriz)", trecho)

    def test_template_oferece_importacao_csv(self):
        self.assertIn("titulos_importar_csv", self.template)

    def test_importador_declara_layout_congelado(self):
        obrigatorias = [
            "chave_idempotencia", "descricao", "entidade_nome",
            "documento_referencia", "data_emissao", "data_competencia",
            "plano_conta_codigo", "centro_custo_codigo", "valor_bruto",
            "valor_desconto", "valor_juros", "observacao",
            "parcela_numero", "parcela_vencimento", "parcela_valor",
        ]
        for campo in obrigatorias:
            self.assertIn(campo, self.importador)

    def test_importador_usa_csv_delimitado_por_ponto_e_virgula(self):
        self.assertIn("csv.", self.importador)
        self.assertIn('delimiter=";"', self.importador)

    def test_importador_limita_natureza_a_pagar(self):
        self.assertIn("TituloFinanceiro.Natureza.PAGAR", self.importador)

    def test_importador_resolve_plano_e_centro_por_codigo_na_matriz(self):
        self.assertIn("PlanoConta", self.importador)
        self.assertIn("CentroCusto", self.importador)
        self.assertIn("plano_conta_codigo", self.importador)
        self.assertIn("centro_custo_codigo", self.importador)
        self.assertIn("matriz=matriz", self.importador)

    def test_importador_agrupa_parcelas_por_chave_idempotencia(self):
        self.assertIn("chave_idempotencia", self.importador)
        self.assertIn("parcela_numero", self.importador)
        self.assertIn("parcela_vencimento", self.importador)
        self.assertIn("parcela_valor", self.importador)

    def test_importador_reutiliza_servico_financeiro_existente(self):
        self.assertIn("criar_lancamento_manual", self.importador)

    def test_importacao_e_atomica(self):
        self.assertTrue(
            "@transaction.atomic" in self.importador or "transaction.atomic()" in self.importador,
            "A importacao inteira deve ser all-or-nothing.",
        )

    def test_importador_possui_validacao_previa_com_linha_e_campo(self):
        self.assertIn("linha", self.importador.lower())
        self.assertIn("campo", self.importador.lower())
        self.assertIn("ValidationError", self.importador)

    def test_importador_nao_confia_loja_livre_do_csv(self):
        self.assertNotIn("loja_codigo", self.importador)
        self.assertNotIn("loja_nome", self.importador)