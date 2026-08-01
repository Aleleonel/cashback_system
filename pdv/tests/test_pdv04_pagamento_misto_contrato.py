from pathlib import Path

from django.test import SimpleTestCase


class PagamentoMistoFrontendContratoTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        root = Path(__file__).resolve().parents[2]
        cls.js = (
            root / "pdv" / "static" / "pdv" / "js" / "frente_caixa.js"
        ).read_text(encoding="utf-8-sig")
        cls.fechamento = (
            root / "pdv" / "services" / "vendas" / "fechamento.py"
        ).read_text(encoding="utf-8-sig")

    def test_recebido_e_editavel_em_todas_as_formas(self):
        self.assertIn("recebido.disabled = false;", self.js)
        self.assertNotIn("recebido.disabled = !forma.permite_troco;", self.js)

    def test_pix_debito_e_credito_sincronizam_recebido_com_valor(self):
        self.assertIn("origem === recebido", self.js)
        self.assertIn("valor.value = numero(recebido.value)", self.js)

    def test_nova_linha_recebe_automaticamente_o_restante(self):
        self.assertIn("const restante = resumoPagamentos().restante;", self.js)
        self.assertIn(
            'adicionarPagamento(restante > 0 ? restante.toFixed(2) : "")',
            self.js,
        )

    def test_finalizacao_bloqueia_falta_ou_excesso(self):
        self.assertIn("Ainda falta receber", self.js)
        self.assertIn("Os pagamentos excedem o total", self.js)
        self.assertIn("if (!resumo.quitado)", self.js)

    def test_troco_permanece_exclusivo_do_dinheiro(self):
        self.assertIn("forma.permite_troco && recebido < valor", self.js)
        self.assertIn(
            "!forma.permite_troco && Math.abs(recebido - valor)",
            self.js,
        )

    def test_backend_aceita_lista_e_soma_valores_parciais(self):
        self.assertIn("for indice, dados in enumerate(pagamentos, 1)", self.fechamento)
        self.assertIn("soma += valor", self.fechamento)
        self.assertIn("if soma != venda.total", self.fechamento)
