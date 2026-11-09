"""F32P3D: contratos de validacao de sessao de caixa no Atacado."""
from types import SimpleNamespace
from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.test import SimpleTestCase
from atacado.integracao_pdv import validar_contexto_consolidacao
from atacado.models import StatusPedidoAtacado
from pdv.choices import StatusSessaoCaixa


class GuardasSessaoAtacadoTests(SimpleTestCase):
    def setUp(self):
        self.pedido = SimpleNamespace(
            status=StatusPedidoAtacado.GERADO, venda_pdv_id=None,
            loja_id=10, matriz_id=20, vendedor_id=30,
        )
        self.operador = SimpleNamespace(pk=40, is_active=True)
        self.sessao = SimpleNamespace(pk=50)
        self.sessao_banco = SimpleNamespace(
            status=StatusSessaoCaixa.ABERTA,
            caixa=SimpleNamespace(loja_id=10, loja=SimpleNamespace(matriz_id=20)),
        )

    def validar(self):
        with patch('atacado.integracao_pdv.SessaoCaixa.objects') as manager:
            manager.select_related.return_value.get.return_value = self.sessao_banco
            return validar_contexto_consolidacao(
                pedido=self.pedido, sessao_caixa=self.sessao, operador=self.operador,
            )

    def test_sessao_aberta_mesma_loja_e_matriz(self):
        self.assertIs(self.validar(), self.sessao_banco)

    def test_pedido_ja_vinculado_nao_pode_consolidar(self):
        self.pedido.venda_pdv_id = 99
        with self.assertRaises(ValidationError):
            self.validar()

    def test_pedido_nao_gerado_nao_pode_consolidar(self):
        self.pedido.status = StatusPedidoAtacado.FINALIZADO
        with self.assertRaises(ValidationError):
            self.validar()

    def test_operador_inativo_nao_pode_consolidar(self):
        self.operador.is_active = False
        with self.assertRaises(ValidationError):
            self.validar()

    def test_sessao_fechada_nao_pode_consolidar(self):
        self.sessao_banco.status = 'FECHADA'
        with self.assertRaises(ValidationError):
            self.validar()

    def test_sessao_de_outra_loja_nao_pode_consolidar(self):
        self.sessao_banco.caixa.loja_id = 999
        with self.assertRaises(ValidationError):
            self.validar()

    def test_sessao_de_outra_matriz_nao_pode_consolidar(self):
        self.sessao_banco.caixa.loja.matriz_id = 999
        with self.assertRaises(ValidationError):
            self.validar()

    def test_pedido_sem_vendedor_nao_pode_consolidar(self):
        self.pedido.vendedor_id = None
        with self.assertRaises(ValidationError):
            self.validar()

    def test_sessao_ausente_nao_pode_consolidar(self):
        self.sessao = None
        with self.assertRaises(ValidationError):
            self.validar()
