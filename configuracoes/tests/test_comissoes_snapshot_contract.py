from decimal import Decimal
from django.core.exceptions import ValidationError
from django.test import TestCase
from empresas.models import Matriz, Loja
from accounts.models import Usuario
from configuracoes.models import FechamentoComissao, ComissaoVendedor


class SnapshotComissoesContractTests(TestCase):
    def setUp(self):
        self.matriz = Matriz.objects.create(nome="Matriz Comissao Snapshot")
        self.loja = Loja.objects.create(matriz=self.matriz, nome="Loja Comissao Snapshot")
        self.vendedor = Usuario.objects.create_user(
            username="vend_snapshot", password="x", matriz=self.matriz
        )

    def test_fechamento_congela_competencia_e_parametros(self):
        f = FechamentoComissao(
            matriz=self.matriz, loja=self.loja,
            competencia_ano=2026, competencia_mes=10,
            total_vendas_loja=Decimal("82000.00"),
            valor_meta_atingida=Decimal("70000.00"),
            percentual_aplicado=Decimal("3.0000"),
            exigir_minimo_individual=True,
            minimo_individual=Decimal("10000.00"),
        )
        f.full_clean()
        f.save()
        self.assertEqual(f.competencia_ano, 2026)
        self.assertEqual(f.competencia_mes, 10)

    def test_um_fechamento_por_loja_e_competencia(self):
        campos = dict(
            matriz=self.matriz, loja=self.loja,
            competencia_ano=2026, competencia_mes=10,
            total_vendas_loja=Decimal("82000.00"),
            valor_meta_atingida=Decimal("70000.00"),
            percentual_aplicado=Decimal("3.0000"),
            exigir_minimo_individual=False,
            minimo_individual=Decimal("0.00"),
        )
        FechamentoComissao.objects.create(**campos)
        with self.assertRaises(ValidationError):
            duplicado = FechamentoComissao(**campos)
            duplicado.full_clean()

    def test_detalhe_congela_identidade_producao_e_comissao(self):
        f = FechamentoComissao.objects.create(
            matriz=self.matriz, loja=self.loja,
            competencia_ano=2026, competencia_mes=10,
            total_vendas_loja=Decimal("82000.00"),
            valor_meta_atingida=Decimal("70000.00"),
            percentual_aplicado=Decimal("3.0000"),
            exigir_minimo_individual=True,
            minimo_individual=Decimal("10000.00"),
        )
        d = ComissaoVendedor(
            fechamento=f, vendedor=self.vendedor,
            vendedor_uuid_original=self.vendedor.uuid,
            vendedor_nome_original=self.vendedor.get_full_name() or self.vendedor.username,
            total_vendas_vendedor=Decimal("18000.00"),
            elegivel=True, valor_comissao=Decimal("540.00"),
        )
        d.full_clean()
        d.save()
        self.assertEqual(d.valor_comissao, Decimal("540.00"))

    def test_um_detalhe_por_vendedor_no_fechamento(self):
        f = FechamentoComissao.objects.create(
            matriz=self.matriz, loja=self.loja,
            competencia_ano=2026, competencia_mes=10,
            total_vendas_loja=Decimal("82000.00"),
            valor_meta_atingida=Decimal("70000.00"),
            percentual_aplicado=Decimal("3.0000"),
            exigir_minimo_individual=False,
            minimo_individual=Decimal("0.00"),
        )
        base = dict(
            fechamento=f, vendedor=self.vendedor,
            vendedor_uuid_original=self.vendedor.uuid,
            vendedor_nome_original=self.vendedor.username,
            total_vendas_vendedor=Decimal("18000.00"),
            elegivel=True, valor_comissao=Decimal("540.00"),
        )
        ComissaoVendedor.objects.create(**base)
        with self.assertRaises(ValidationError):
            dup = ComissaoVendedor(**base)
            dup.full_clean()
    def test_snapshot_fechamento_e_detalhe_sao_imutaveis(self):
        f = FechamentoComissao.objects.create(
            matriz=self.matriz, loja=self.loja,
            competencia_ano=2026, competencia_mes=10,
            total_vendas_loja=Decimal("82000.00"),
            valor_meta_atingida=Decimal("70000.00"),
            percentual_aplicado=Decimal("3.0000"),
            exigir_minimo_individual=True,
            minimo_individual=Decimal("10000.00"),
        )
        d = ComissaoVendedor.objects.create(
            fechamento=f, vendedor=self.vendedor,
            vendedor_uuid_original=self.vendedor.uuid,
            vendedor_nome_original=self.vendedor.username,
            total_vendas_vendedor=Decimal("18000.00"),
            elegivel=True, valor_comissao=Decimal("540.00"),
        )
        f.total_vendas_loja = Decimal("99999.00")
        with self.assertRaises(ValidationError):
            f.save()
        with self.assertRaises(ValidationError):
            f.delete()
        d.valor_comissao = Decimal("999.00")
        with self.assertRaises(ValidationError):
            d.save()
        with self.assertRaises(ValidationError):
            d.delete()
    def test_fechamento_rejeita_loja_de_outra_matriz(self):
        from empresas.models import Matriz, Loja

        outra_matriz = Matriz.objects.create(nome="Outra Matriz")
        outra_loja = Loja.objects.create(
            matriz=outra_matriz,
            nome="Outra Loja",
        )
        fechamento = FechamentoComissao(
            matriz=self.matriz,
            loja=outra_loja,
            competencia_ano=2026,
            competencia_mes=10,
            total_vendas_loja=Decimal("82000.00"),
            valor_meta_atingida=Decimal("70000.00"),
            percentual_aplicado=Decimal("3.0000"),
            exigir_minimo_individual=True,
            minimo_individual=Decimal("10000.00"),
        )
        with self.assertRaises(ValidationError):
            fechamento.save()