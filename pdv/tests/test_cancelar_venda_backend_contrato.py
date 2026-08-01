from pathlib import Path

from django.test import SimpleTestCase


class CancelarVendaBackendContratoTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        root = Path(__file__).resolve().parents[2]

        cls.views = (
            root / "pdv" / "views.py"
        ).read_text(encoding="utf-8-sig")

        cls.servico = (
            root / "pdv" / "services" / "vendas" / "cancelamento.py"
        ).read_text(encoding="utf-8-sig")

    def test_view_delega_cancelamento_para_servico(self):
        self.assertIn(
            "def cancelar_venda_web",
            self.views,
        )
        self.assertIn(
            "cancelar_venda(",
            self.views,
        )
        self.assertIn(
            "venda=venda",
            self.views,
        )
        self.assertIn(
            "usuario=request.user",
            self.views,
        )

    def test_mantem_bloqueio_de_venda_finalizada(self):
        self.assertIn(
            "StatusOperacaoVenda.FINALIZADA",
            self.servico,
        )
        self.assertIn(
            "ValidationError",
            self.servico,
        )

    def test_mantem_cancelamento_do_status(self):
        self.assertIn(
            "venda.status = StatusOperacaoVenda.CANCELADA",
            self.servico,
        )
        self.assertIn(
            '"status"',
            self.servico,
        )

    def test_servico_permanece_transacional(self):
        self.assertIn(
            "@transaction.atomic",
            self.servico,
        )

    def test_view_nao_duplicou_regra_de_status(self):
        inicio = self.views.find("def cancelar_venda_web")
        self.assertGreaterEqual(inicio, 0)

        restante = self.views[inicio:]
        proximos = [
            posicao
            for posicao in (
                restante.find("\n@"),
                restante.find("\ndef "),
            )
            if posicao > 0
        ]
        fim = min(proximos) if proximos else len(restante)
        funcao = restante[:fim]

        self.assertNotIn(
            "venda.status = StatusOperacaoVenda.CANCELADA",
            funcao,
        )
        self.assertIn(
            "cancelar_venda(",
            funcao,
        )