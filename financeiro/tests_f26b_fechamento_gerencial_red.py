from pathlib import Path
from django.test import SimpleTestCase

ROOT = Path(__file__).resolve().parents[1]
MODELS = (ROOT / "financeiro" / "models.py").read_text(encoding="utf-8")
SERVICES = (ROOT / "financeiro" / "services.py").read_text(encoding="utf-8")


class F26BFechamentoGerencialContratoRED(SimpleTestCase):
    def test_existe_modelo_periodo_fechamento_gerencial(self):
        self.assertIn("class FechamentoGerencial", MODELS)

    def test_fechamento_e_matricial_por_competencia(self):
        bloco = MODELS[MODELS.find("class FechamentoGerencial"):]
        for token in ("matriz", "competencia_ano", "competencia_mes"):
            self.assertIn(token, bloco)

    def test_status_aberto_e_fechado_sao_explicitos(self):
        bloco = MODELS[MODELS.find("class FechamentoGerencial"):]
        self.assertIn("ABERTO", bloco)
        self.assertIn("FECHADO", bloco)

    def test_competencia_e_unica_por_matriz(self):
        bloco = MODELS[MODELS.find("class FechamentoGerencial"):]
        self.assertIn("UniqueConstraint", bloco)
        self.assertIn("competencia_ano", bloco)
        self.assertIn("competencia_mes", bloco)

    def test_fechamento_registra_responsavel_e_instante(self):
        bloco = MODELS[MODELS.find("class FechamentoGerencial"):]
        self.assertIn("fechado_por", bloco)
        self.assertIn("fechado_em", bloco)

    def test_reabertura_e_auditavel(self):
        bloco = MODELS[MODELS.find("class FechamentoGerencial"):]
        self.assertIn("reaberto_por", bloco)
        self.assertIn("reaberto_em", bloco)
        self.assertIn("motivo_reabertura", bloco)

    def test_servico_de_validacao_pre_fechamento_existe(self):
        self.assertIn("validar_fechamento_gerencial", SERVICES)

    def test_servico_de_fechamento_existe(self):
        self.assertIn("fechar_competencia_gerencial", SERVICES)

    def test_servico_de_reabertura_existe(self):
        self.assertIn("reabrir_competencia_gerencial", SERVICES)

    def test_contrato_nao_usa_baixa_como_competencia_economica(self):
        # Baixa continua sendo fato de caixa; fechamento gerencial deve trabalhar
        # com competencia economica e snapshots/fontes ja consolidadas.
        bloco = SERVICES[SERVICES.find("def validar_fechamento_gerencial"):]
        if bloco:
            self.assertNotIn("data_competencia = baixa", bloco.lower())