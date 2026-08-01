from pathlib import Path

from django.test import SimpleTestCase


class VoucherPosFinalizacaoContratoTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        root = Path(__file__).resolve().parents[2]

        cls.fechamento = (
            root / "pdv" / "services" / "vendas" / "fechamento.py"
        ).read_text(encoding="utf-8-sig")

        cls.beneficios = (
            root / "pdv" / "services" / "vendas" / "beneficios.py"
        ).read_text(encoding="utf-8-sig")

        cls.utilizacao = (
            root / "vouchers" / "services" / "utilizacao.py"
        ).read_text(encoding="utf-8-sig")

        cls.javascript = (
            root / "pdv" / "static" / "pdv" / "js" / "frente_caixa.js"
        ).read_text(encoding="utf-8-sig")

    def test_finalizacao_delega_resolucao_ao_adapter(self):
        self.assertIn(
            "resolver_beneficio_da_venda(",
            self.fechamento,
        )
        self.assertNotIn(
            "UsoVoucher.objects.create(",
            self.fechamento,
        )

    def test_adapter_delega_registro_ao_servico_oficial(self):
        self.assertIn(
            "def registrar_voucher_da_venda(",
            self.beneficios,
        )
        self.assertIn(
            "registrar_uso_voucher(",
            self.beneficios,
        )

    def test_servico_oficial_registra_uso_do_voucher(self):
        self.assertIn(
            "UsoVoucher.objects.create(",
            self.utilizacao,
        )
        self.assertIn(
            "valor_desconto=valor_desconto",
            self.utilizacao,
        )
        self.assertIn(
            "voucher=voucher_bloqueado",
            self.utilizacao,
        )

    def test_voucher_e_bloqueado_para_atualizacao(self):
        self.assertIn(
            "Voucher.objects.select_for_update().get(",
            self.utilizacao,
        )
        self.assertIn(
            "voucher_bloqueado.total_utilizado >= voucher_bloqueado.limite_utilizacao",
            self.utilizacao,
        )

    def test_finalizacao_limpa_voucher_visual(self):
        marcador = 'mostrarAlerta(payload.mensagem || "Venda finalizada com sucesso."'
        self.assertIn(marcador, self.javascript)

        trecho_inicio = self.javascript.index(marcador)
        contexto = self.javascript[max(0, trecho_inicio - 400):trecho_inicio + 400]

        self.assertIn("voucherAplicado = null;", contexto)
        self.assertIn("renderVoucherAplicado();", contexto)
        self.assertIn("limparModalFechamento();", contexto)
        self.assertIn("await carregarEstado();", contexto)

    def test_pagamento_misto_permanece_intacto(self):
        self.assertIn("const resumoPagamentos = () => {", self.javascript)
        self.assertIn(
            "const atualizarLinha = (linha, origem = null) => {",
            self.javascript,
        )
        self.assertIn(
            'const adicionarPagamento = (valor = "") => {',
            self.javascript,
        )
        self.assertIn("def _registrar_pagamentos(", self.fechamento)
        self.assertIn("soma", self.fechamento)
        self.assertIn("venda.total", self.fechamento)
        self.assertIn("pagamentos", self.fechamento)