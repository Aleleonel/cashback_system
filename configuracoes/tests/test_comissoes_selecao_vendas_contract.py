from datetime import datetime
from decimal import Decimal
from types import SimpleNamespace
from django.test import SimpleTestCase
from django.utils import timezone

from configuracoes.services_comissoes import selecionar_vendas_validas_competencia


class FakeQuerySet:
    def __init__(self, rows):
        self.rows = list(rows)
        self.filters = []

    def filter(self, **kwargs):
        self.filters.append(kwargs)
        rows = self.rows
        for key, value in kwargs.items():
            if key == "loja_id":
                rows = [r for r in rows if r.loja_id == value]
            elif key == "status":
                rows = [r for r in rows if r.status == value]
            elif key == "finalizada_em__gte":
                rows = [r for r in rows if r.finalizada_em >= value]
            elif key == "finalizada_em__lt":
                rows = [r for r in rows if r.finalizada_em < value]
            elif key == "cancelada_em__isnull":
                rows = [r for r in rows if (r.cancelada_em is None) == value]
            else:
                raise AssertionError(f"Filtro inesperado: {key}")
        clone = FakeQuerySet(rows)
        clone.filters = self.filters
        return clone

    def __iter__(self):
        return iter(self.rows)


class SelecaoVendasCompetenciaContractTests(SimpleTestCase):
    def dt(self, ano, mes, dia):
        return timezone.make_aware(datetime(ano, mes, dia, 12, 0, 0))

    def test_filtra_loja_mes_finalizada_e_exclui_canceladas(self):
        rows = [
            SimpleNamespace(id=1, loja_id=10, vendedor_id=101, total=Decimal("100.00"), status="finalizada", finalizada_em=self.dt(2026,10,1), cancelada_em=None),
            SimpleNamespace(id=2, loja_id=10, vendedor_id=101, total=Decimal("200.00"), status="finalizada", finalizada_em=self.dt(2026,10,31), cancelada_em=None),
            SimpleNamespace(id=3, loja_id=10, vendedor_id=101, total=Decimal("999.00"), status="finalizada", finalizada_em=self.dt(2026,10,15), cancelada_em=self.dt(2026,10,16)),
            SimpleNamespace(id=4, loja_id=10, vendedor_id=101, total=Decimal("888.00"), status="finalizada", finalizada_em=self.dt(2026,9,30), cancelada_em=None),
            SimpleNamespace(id=5, loja_id=20, vendedor_id=101, total=Decimal("777.00"), status="finalizada", finalizada_em=self.dt(2026,10,15), cancelada_em=None),
        ]
        qs = FakeQuerySet(rows)
        selecionadas = list(selecionar_vendas_validas_competencia(qs, loja_id=10, ano=2026, mes=10))
        self.assertEqual([v.id for v in selecionadas], [1, 2])

    def test_competencia_tem_limites_inicio_inclusivo_proximo_mes_exclusivo(self):
        rows = [
            SimpleNamespace(id=1, loja_id=10, vendedor_id=101, total=Decimal("100.00"), status="finalizada", finalizada_em=timezone.make_aware(datetime(2026,10,1,0,0,0)), cancelada_em=None),
            SimpleNamespace(id=2, loja_id=10, vendedor_id=101, total=Decimal("200.00"), status="finalizada", finalizada_em=timezone.make_aware(datetime(2026,11,1,0,0,0)), cancelada_em=None),
        ]
        selecionadas = list(selecionar_vendas_validas_competencia(FakeQuerySet(rows), loja_id=10, ano=2026, mes=10))
        self.assertEqual([v.id for v in selecionadas], [1])