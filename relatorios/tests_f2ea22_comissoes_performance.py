from django.test import TestCase
from django.db import connection
from django.test.utils import CaptureQueriesContext

from configuracoes.models import FechamentoComissao, ComissaoVendedor


class RelatorioComissoesPerformanceContratoTest(TestCase):
    """Contrato estrutural: relacionamentos exibidos nao podem gerar N+1."""

    def test_queryset_fechamentos_carrega_loja_sem_query_adicional(self):
        qs = FechamentoComissao.objects.select_related("loja").order_by(
            "-competencia_ano", "-competencia_mes", "loja__nome", "id"
        )
        with CaptureQueriesContext(connection) as ctx:
            rows = list(qs[:50])
            for item in rows:
                _ = item.loja.nome
        self.assertLessEqual(len(ctx), 1)

    def test_queryset_comissoes_carrega_relacionamentos_sem_query_adicional(self):
        qs = ComissaoVendedor.objects.select_related(
            "fechamento", "fechamento__loja", "vendedor"
        ).order_by(
            "-fechamento__competencia_ano",
            "-fechamento__competencia_mes",
            "fechamento__loja__nome",
            "vendedor_nome_original",
            "id",
        )
        with CaptureQueriesContext(connection) as ctx:
            rows = list(qs[:50])
            for item in rows:
                _ = item.fechamento.competencia_ano
                _ = item.fechamento.competencia_mes
                _ = item.fechamento.loja.nome
                _ = item.vendedor
                _ = item.vendedor_nome_original
                _ = item.total_vendas_vendedor
                _ = item.elegivel
                _ = item.valor_comissao
        self.assertLessEqual(len(ctx), 1)