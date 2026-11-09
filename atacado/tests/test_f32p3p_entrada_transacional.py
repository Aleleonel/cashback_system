"""F32P3P: teste RED de integridade de entrada com banco Django isolado."""
from django.core.exceptions import ValidationError
from atacado.tests.test_f32j_ciclo_operacional import F32JCicloOperacionalTests
from atacado.integracao_transacional_pdv import consolidar_pedido_atacado_pdv


class EntradaTransacionalF32P3PTests(F32JCicloOperacionalTests):
    """Reutiliza fixtures reais de matriz, loja, cliente, produto e pedido."""
    def test_sessao_ausente_deve_ser_erro_de_dominio_sem_escritas(self):
        from pdv.models import Venda
        pedido = self.pedido()
        antes = Venda.objects.count()
        with self.assertRaises(ValidationError):
            consolidar_pedido_atacado_pdv(
                pedido=pedido, sessao_caixa=None, operador=None, pagamentos=[]
            )
        pedido.refresh_from_db()
        self.assertIsNone(pedido.venda_pdv_id)
        self.assertEqual(Venda.objects.count(), antes)