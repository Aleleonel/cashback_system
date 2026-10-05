from django.test import TestCase
from configuracoes.services_comissoes import fechar_comissoes_competencia

class FechamentoPersistidoFuncionalContractTest(TestCase):
    def test_funcao_expoe_contrato_operacional_sem_recalculo(self):
        import inspect
        fonte = inspect.getsource(fechar_comissoes_competencia)
        self.assertIn("return existente", fonte)
        self.assertIn("transaction.atomic", fonte)
        self.assertIn("select_for_update", fonte)
        self.assertIn("venda.vendedor_id is not None", fonte)

    def test_funcao_persiste_snapshots_necessarios(self):
        import inspect
        fonte = inspect.getsource(fechar_comissoes_competencia)
        for trecho in (
            "total_vendas_loja=resultado.total_loja",
            "percentual_aplicado=resultado.percentual_aplicado",
            "vendedor_uuid_original=vendedor.uuid",
            "vendedor_nome_original=nome",
            "total_vendas_vendedor=total_vendedor",
            "valor_comissao=resultado.comissoes.get",
        ):
            self.assertIn(trecho, fonte)

    def test_idempotencia_deve_ser_protegida_contra_corrida_por_chave_da_competencia(self):
        import inspect
        fonte = inspect.getsource(fechar_comissoes_competencia)
        self.assertIn("IntegrityError", fonte)