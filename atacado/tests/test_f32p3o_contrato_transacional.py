"""F32P3O: verificacoes estaticas das invariantes do servico; nao substituem testes de banco."""
import ast
from pathlib import Path
from django.test import SimpleTestCase

SERVICE = Path(__file__).resolve().parents[1] / 'integracao_transacional_pdv.py'

class ContratoTransacionalF32P3OTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.tree = ast.parse(SERVICE.read_text(encoding='utf-8'))
        cls.source = SERVICE.read_text(encoding='utf-8')
        cls.functions = {n.name: n for n in cls.tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}

    def test_servico_existe_e_e_atomico(self):
        fn = self.functions['consolidar_pedido_atacado_pdv']
        self.assertTrue(any(isinstance(d, ast.Attribute) and d.attr == 'atomic' for d in fn.decorator_list))

    def test_lock_pedido_e_sessao(self):
        self.assertGreaterEqual(self.source.count('select_for_update()'), 2)

    def test_vinculo_a_sessao_e_modalidade_atacado(self):
        self.assertIn('sessao_caixa=sessao', self.source)
        self.assertIn('modalidade=ModalidadeComercial.ATACADO', self.source)

    def test_nao_confirma_reservas_pdv(self):
        self.assertIn('_reservas_ativas_pedido(pedido)', self.source)
        self.assertNotIn('confirmar_reservas_itens_venda', self.source)

    def test_financeiro_e_auditoria(self):
        self.assertIn('registrar_movimentacao_caixa_venda(', self.source)
        self.assertIn('gerar_contas_receber_venda(', self.source)
        self.assertIn('registrar_auditoria_finalizacao_venda(', self.source)

    def test_idempotencia_estrutural(self):
        self.assertIn('pedido.venda_pdv_id', self.source)
        self.assertIn('return venda', self.source)