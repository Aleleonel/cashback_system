from pathlib import Path
from django.test import SimpleTestCase

MODELS = Path(__file__).with_name("models.py").read_text(encoding="utf-8")


class CadastrosMestresFinanceiroContractTests(SimpleTestCase):
    def test_plano_conta_existe_com_escopo_matriz(self):
        self.assertIn("class PlanoConta", MODELS)
        for token in (
            "matriz",
            "codigo",
            "nome",
            "tipo",
            "natureza",
            "pai",
            "nivel",
            "aceita_lancamento",
            "ativo",
        ):
            self.assertIn(token, MODELS)

    def test_plano_conta_tem_tipos_e_naturezas_congelados(self):
        for token in (
            "SINTETICA",
            "ANALITICA",
            "DESPESA",
            "RECEITA",
            "ATIVO",
            "PASSIVO",
            "OUTRO",
        ):
            self.assertIn(token, MODELS)

    def test_plano_conta_tem_hierarquia_protect_e_unique_matriz_codigo(self):
        self.assertIn('"self"', MODELS)
        self.assertIn("models.PROTECT", MODELS)
        self.assertIn("UniqueConstraint", MODELS)
        self.assertIn('"matriz", "codigo"', MODELS)

    def test_centro_custo_existe_e_pertence_matriz(self):
        self.assertIn("class CentroCusto", MODELS)
        for token in ("matriz", "codigo", "nome", "descricao", "ativo"):
            self.assertIn(token, MODELS)
        self.assertIn('"matriz", "codigo"', MODELS)

    def test_instituicao_bancaria_existe_com_codigo_bacen(self):
        self.assertIn("class InstituicaoBancaria", MODELS)
        for token in ("codigo_bacen", "nome", "ativo"):
            self.assertIn(token, MODELS)

    def test_conta_financeira_existe_com_escopo_e_dados_bancarios(self):
        self.assertIn("class ContaFinanceira", MODELS)
        for token in (
            "matriz",
            "loja",
            "instituicao",
            "tipo",
            "nome",
            "agencia",
            "numero",
            "digito",
            "chave_pix",
            "ativo",
        ):
            self.assertIn(token, MODELS)

    def test_conta_financeira_tem_tipos_congelados(self):
        for token in (
            "CONTA_CORRENTE",
            "POUPANCA",
            "CARTEIRA_DIGITAL",
            "OUTRA",
        ):
            self.assertIn(token, MODELS)

    def test_cadastros_mestres_usam_uuid_e_timestamps_quando_previstos(self):
        self.assertGreaterEqual(MODELS.count("UUIDField"), 4)
        self.assertGreaterEqual(MODELS.count("criado_em"), 3)
        self.assertGreaterEqual(MODELS.count("atualizado_em"), 3)

    def test_conta_financeira_nao_persiste_saldo(self):
        inicio = MODELS.find("class ContaFinanceira")
        self.assertGreaterEqual(inicio, 0)
        trecho = MODELS[inicio:]
        self.assertNotIn("saldo =", trecho)
        self.assertNotIn("saldo=models.", trecho.replace(" ", ""))

    def test_modelos_nao_criam_segundo_caixa_pdv(self):
        self.assertNotIn("class CaixaFinanceiro", MODELS)
        self.assertNotIn("class SessaoCaixaFinanceiro", MODELS)