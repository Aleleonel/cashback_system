from pathlib import Path
from django.test import SimpleTestCase

ROOT = Path(__file__).resolve().parent.parent
MODELS = ROOT / "financeiro" / "models.py"


class ModelosFinanceirosContractRedTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.texto = MODELS.read_text(encoding="utf-8")

    def test_modelos_devem_ser_persistentes(self):
        self.assertNotIn("abstract = True", self.texto)

    def test_titulo_deve_conter_campos_congelados(self):
        for token in (
            "uuid = models.UUIDField",
            "matriz = models.ForeignKey",
            "loja = models.ForeignKey",
            "natureza = models.CharField",
            "origem_tipo = models.CharField",
            "origem_id = models.CharField",
            "chave_idempotencia = models.CharField",
            "descricao = models.CharField",
            "valor_original = models.DecimalField",
            "status = models.CharField",
            "data_emissao = models.DateField",
            "criado_em = models.DateTimeField",
            "atualizado_em = models.DateTimeField",
        ):
            self.assertIn(token, self.texto)

    def test_parcela_deve_conter_campos_congelados(self):
        for token in (
            "titulo = models.ForeignKey",
            "numero = models.PositiveSmallIntegerField",
            "vencimento = models.DateField",
            "valor_original = models.DecimalField",
            "status = models.CharField",
            "criado_em = models.DateTimeField",
        ):
            self.assertIn(token, self.texto)

    def test_baixa_deve_conter_campos_congelados(self):
        for token in (
            "parcela = models.ForeignKey",
            "valor = models.DecimalField",
            "data = models.DateField",
            "tipo = models.CharField",
            "chave_idempotencia = models.CharField",
            "observacao = models.TextField",
            "criado_em = models.DateTimeField",
        ):
            self.assertIn(token, self.texto)

    def test_choices_de_dominio_devem_existir(self):
        for token in (
            'PAGAR = "PAGAR"',
            'RECEBER = "RECEBER"',
            'ABERTO = "ABERTO"',
            'PARCIAL = "PARCIAL"',
            'LIQUIDADO = "LIQUIDADO"',
            'CANCELADO = "CANCELADO"',
            'BAIXA = "BAIXA"',
            'ESTORNO = "ESTORNO"',
        ):
            self.assertIn(token, self.texto)

    def test_constraints_congeladas_devem_existir(self):
        for token in (
            "models.UniqueConstraint",
            "models.CheckConstraint",
            "fields=[\"matriz\", \"chave_idempotencia\"]",
            "fields=[\"matriz\", \"natureza\", \"origem_tipo\", \"origem_id\"]",
            "fields=[\"titulo\", \"numero\"]",
        ):
            self.assertIn(token, self.texto)

    def test_indices_congelados_devem_existir(self):
        for token in (
            "fields=[\"matriz\", \"natureza\", \"status\"]",
            "fields=[\"matriz\", \"loja\", \"status\"]",
            "fields=[\"origem_tipo\", \"origem_id\"]",
            "fields=[\"vencimento\", \"status\"]",
            "fields=[\"titulo\", \"status\"]",
            "fields=[\"parcela\", \"data\"]",
        ):
            self.assertIn(token, self.texto)

    def test_valores_monetarios_devem_usar_14_2(self):
        self.assertGreaterEqual(self.texto.count("max_digits=14"), 3)
        self.assertGreaterEqual(self.texto.count("decimal_places=2"), 3)

    def test_relacoes_consolidadas_devem_usar_protect(self):
        self.assertEqual(self.texto.count("on_delete=models.PROTECT"), 4)