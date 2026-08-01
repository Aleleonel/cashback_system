from pathlib import Path

from django.test import SimpleTestCase


class VoucherSemRegressaoContratoTests(SimpleTestCase):
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

        cls.validacoes = (
            root / "cashback" / "services" / "validacoes.py"
        ).read_text(encoding="utf-8-sig")

        cls.javascript = (
            root / "pdv" / "static" / "pdv" / "js" / "frente_caixa.js"
        ).read_text(encoding="utf-8-sig")

    def test_fechamento_nao_repete_regras_internas_de_voucher(self):
        self.assertNotIn(
            "Este cliente ja utilizou este voucher.",
            self.fechamento,
        )
        self.assertNotIn(
            "UsoVoucher.objects.create(",
            self.fechamento,
        )
        self.assertNotIn(
            "Voucher.objects.select_for_update()",
            self.fechamento,
        )

    def test_fechamento_delega_resolucao_de_beneficio(self):
        self.assertIn(
            "resolver_beneficio_da_venda(",
            self.fechamento,
        )

    def test_adapter_delega_persistencia_do_voucher(self):
        self.assertIn(
            "registrar_uso_voucher(",
            self.beneficios,
        )

    def test_uso_do_voucher_continua_registrado(self):
        self.assertIn(
            "UsoVoucher.objects.create(",
            self.utilizacao,
        )
        self.assertIn(
            "voucher=voucher_bloqueado",
            self.utilizacao,
        )
        self.assertIn(
            "cliente=cliente",
            self.utilizacao,
        )
        self.assertIn(
            "valor_desconto=valor_desconto",
            self.utilizacao,
        )

    def test_limite_global_do_voucher_continua_protegido(self):
        self.assertIn(
            "Voucher.objects.select_for_update().get(",
            self.utilizacao,
        )
        self.assertIn(
            "voucher_bloqueado.total_utilizado >= voucher_bloqueado.limite_utilizacao",
            self.utilizacao,
        )
        self.assertIn(
            "total_utilizado__lt=F('limite_utilizacao')",
            self.utilizacao,
        )

    def test_regra_de_cliente_permanece_compartilhada(self):
        self.assertIn(
            "def validar_regras_cliente_voucher(",
            self.validacoes,
        )
        self.assertIn(
            "validar_regras_cliente_voucher(",
            self.utilizacao,
        )

    def test_limpeza_apos_finalizacao_permanece(self):
        marcador = 'mostrarAlerta(payload.mensagem || "Venda finalizada com sucesso."'
        self.assertIn(marcador, self.javascript)

        indice = self.javascript.index(marcador)
        contexto = self.javascript[max(0, indice - 500):indice + 500]

        self.assertIn("voucherAplicado = null;", contexto)
        self.assertIn("renderVoucherAplicado();", contexto)
        self.assertIn("limparModalFechamento();", contexto)
        self.assertIn("await carregarEstado();", contexto)

    def test_limpeza_no_cancelamento_permanece(self):
        marcador = "const cancelarVenda = async () => {"
        self.assertIn(marcador, self.javascript)

        inicio = self.javascript.index(marcador)
        contexto = self.javascript[inicio:inicio + 2500]

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
        self.assertIn("venda.total", self.fechamento)
        self.assertIn("pagamentos", self.fechamento)