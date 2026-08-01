from pathlib import Path

from django.test import SimpleTestCase


def extrair_funcao(source, assinatura):
    inicio = source.index(assinatura)
    proxima_funcao = source.find("\ndef ", inicio + len(assinatura))

    if proxima_funcao == -1:
        return source[inicio:]

    return source[inicio:proxima_funcao]


class Pdv04HardeningContratoTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        root = Path(__file__).resolve().parents[2]

        cls.fechamento = (
            root / "pdv" / "services" / "vendas" / "fechamento.py"
        ).read_text(encoding="utf-8-sig")

        cls.finalizacao = (
            root / "pdv" / "services" / "vendas" / "finalizacao.py"
        ).read_text(encoding="utf-8-sig")

        cls.cancelamento = (
            root / "pdv" / "services" / "vendas" / "cancelamento.py"
        ).read_text(encoding="utf-8-sig")

        cls.caixa = (
            root / "pdv" / "services" / "vendas" / "caixa.py"
        ).read_text(encoding="utf-8-sig")

        cls.estoque = (
            root / "pdv" / "services" / "vendas" / "estoque.py"
        ).read_text(encoding="utf-8-sig")

        cls.auditoria = (
            root / "pdv" / "services" / "vendas" / "auditoria.py"
        ).read_text(encoding="utf-8-sig")

        cls.views = (
            root / "pdv" / "views.py"
        ).read_text(encoding="utf-8-sig")

        cls.funcao_finalizar = extrair_funcao(
            cls.finalizacao,
            "def finalizar_venda(",
        )

    def test_fechamento_e_transacional_e_bloqueia_venda(self):
        self.assertIn("@transaction.atomic", self.fechamento)
        self.assertIn(
            "Venda.objects.select_for_update()",
            self.fechamento,
        )

    def test_finalizacao_e_transacional_e_bloqueia_venda(self):
        self.assertIn("@transaction.atomic", self.finalizacao)
        self.assertIn(
            ".select_for_update()",
            self.funcao_finalizar,
        )

    def test_finalizacao_reprocessada_e_idempotente(self):
        self.assertIn(
            "if venda.status == StatusOperacaoVenda.FINALIZADA:",
            self.funcao_finalizar,
        )

        trecho_status = self.funcao_finalizar.index(
            "if venda.status == StatusOperacaoVenda.FINALIZADA:"
        )
        trecho_retorno = self.funcao_finalizar.index(
            "return venda",
            trecho_status,
        )
        trecho_reservas = self.funcao_finalizar.index(
            "_confirmar_reservas("
        )

        self.assertLess(trecho_status, trecho_retorno)
        self.assertLess(trecho_retorno, trecho_reservas)

    def test_finalizacao_mantem_ordem_critica(self):
        indice_reservas = self.funcao_finalizar.index(
            "_confirmar_reservas("
        )
        indice_caixa = self.funcao_finalizar.index(
            "registrar_movimentacao_caixa_venda("
        )
        indice_modelo = self.funcao_finalizar.index(
            "_finalizar_modelo("
        )
        indice_auditoria = self.funcao_finalizar.index(
            "registrar_auditoria_finalizacao_venda("
        )

        self.assertLess(indice_reservas, indice_caixa)
        self.assertLess(indice_caixa, indice_modelo)
        self.assertLess(indice_modelo, indice_auditoria)

    def test_cancelamento_e_transacional_e_bloqueia_venda(self):
        self.assertIn("@transaction.atomic", self.cancelamento)
        self.assertIn("Venda.objects", self.cancelamento)
        self.assertIn(".select_for_update()", self.cancelamento)

    def test_cancelamento_impede_venda_finalizada(self):
        self.assertIn(
            "if venda.status == StatusOperacaoVenda.FINALIZADA:",
            self.cancelamento,
        )
        self.assertIn(
            "Venda finalizada nao pode ser cancelada",
            self.cancelamento,
        )

    def test_cancelamento_repetido_nao_repete_operacoes(self):
        self.assertIn(
            "if venda.status == StatusOperacaoVenda.CANCELADA:",
            self.cancelamento,
        )
        self.assertIn("return venda", self.cancelamento)

    def test_caixa_e_transacional_e_bloqueia_sessao(self):
        self.assertIn("@transaction.atomic", self.caixa)
        self.assertIn(".select_for_update()", self.caixa)

    def test_estoque_e_transacional_e_bloqueia_reservas(self):
        self.assertGreaterEqual(
            self.estoque.count("@transaction.atomic"),
            2,
        )
        self.assertGreaterEqual(
            self.estoque.count(".select_for_update()"),
            2,
        )

    def test_fechamento_usa_idempotencia_da_venda(self):
        self.assertIn(
            "executar_venda_idempotente(",
            self.fechamento,
        )
        self.assertIn(
            "chave_idempotencia=venda.uuid",
            self.fechamento,
        )

    def test_auditoria_recebe_contexto_da_operacao(self):
        self.assertIn(
            "def registrar_auditoria_finalizacao_venda(",
            self.auditoria,
        )
        self.assertIn("usuario=usuario", self.auditoria)
        self.assertIn("request=request", self.auditoria)
        self.assertIn("movimentacao_caixa", self.auditoria)

    def test_finalizacao_propaga_usuario_e_request(self):
        self.assertIn("usuario=usuario", self.funcao_finalizar)
        self.assertIn("request=request", self.funcao_finalizar)
        self.assertIn(
            "usuario=usuario or venda.operador",
            self.funcao_finalizar,
        )

    def test_views_delegam_para_servicos(self):
        self.assertIn(
            "venda_finalizada = fechar_venda_web(",
            self.views,
        )
        self.assertIn("cancelar_venda(", self.views)


class Pdv04RollbackEstruturalContratoTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        root = Path(__file__).resolve().parents[2]

        cls.finalizacao = (
            root / "pdv" / "services" / "vendas" / "finalizacao.py"
        ).read_text(encoding="utf-8-sig")

        cls.fechamento = (
            root / "pdv" / "services" / "vendas" / "fechamento.py"
        ).read_text(encoding="utf-8-sig")

        cls.cancelamento = (
            root / "pdv" / "services" / "vendas" / "cancelamento.py"
        ).read_text(encoding="utf-8-sig")

        cls.funcao_finalizar = extrair_funcao(
            cls.finalizacao,
            "def finalizar_venda(",
        )

    def test_etapas_da_finalizacao_estao_na_mesma_transacao(self):
        decorador = self.finalizacao.rfind(
            "@transaction.atomic",
            0,
            self.finalizacao.index("def finalizar_venda("),
        )
        funcao = self.finalizacao.index("def finalizar_venda(")

        self.assertGreaterEqual(decorador, 0)
        self.assertLess(decorador, funcao)

        reservas = self.funcao_finalizar.index("_confirmar_reservas(")
        caixa = self.funcao_finalizar.index(
            "registrar_movimentacao_caixa_venda("
        )
        modelo = self.funcao_finalizar.index("_finalizar_modelo(")
        auditoria = self.funcao_finalizar.index(
            "registrar_auditoria_finalizacao_venda("
        )

        self.assertLess(reservas, caixa)
        self.assertLess(caixa, modelo)
        self.assertLess(modelo, auditoria)

    def test_fechamento_inteiro_esta_protegido_por_transacao(self):
        decorador = self.fechamento.index("@transaction.atomic")
        funcao = self.fechamento.index("def fechar_venda_web(")
        bloqueio = self.fechamento.index(
            "select_for_update()",
            funcao,
        )
        finalizacao = self.fechamento.index(
            "finalizar_venda(",
            bloqueio,
        )

        self.assertLess(decorador, funcao)
        self.assertLess(funcao, bloqueio)
        self.assertLess(bloqueio, finalizacao)

    def test_cancelamento_inteiro_esta_protegido_por_transacao(self):
        decorador = self.cancelamento.index("@transaction.atomic")
        funcao = self.cancelamento.index("def cancelar_venda(")
        bloqueio = self.cancelamento.index(
            "select_for_update()",
            funcao,
        )
        cancelamento_item = self.cancelamento.index(
            "cancelar_item_venda(",
            bloqueio,
        )

        self.assertLess(decorador, funcao)
        self.assertLess(funcao, bloqueio)
        self.assertLess(bloqueio, cancelamento_item)