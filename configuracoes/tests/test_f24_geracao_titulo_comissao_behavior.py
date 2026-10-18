from datetime import date
from decimal import Decimal
from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.test import TestCase

from configuracoes.models import ComissaoVendedor, FechamentoComissao
from configuracoes.services_comissoes import gerar_titulo_financeiro_comissao
from empresas.models import Loja, Matriz
from financeiro.models import TituloFinanceiro
from accounts.models import Usuario


class F24GeracaoTituloComissaoBehaviorTests(TestCase):
    def setUp(self):
        self.matriz = Matriz.objects.create(nome="Matriz F24", cnpj="12345678000190")
        self.loja = Loja.objects.create(matriz=self.matriz, nome="Loja F24")
        self.vendedor = Usuario.objects.create_user(username="vendedor_f24", password="x", matriz=self.matriz)
        self.fechamento = FechamentoComissao.objects.create(
            matriz=self.matriz, loja=self.loja, competencia_ano=2026, competencia_mes=9,
            total_vendas_loja=Decimal("10000.00"), valor_meta_atingida=Decimal("10000.00"),
            percentual_aplicado=Decimal("2.0000"), exigir_minimo_individual=False,
            minimo_individual=Decimal("0.00"),
        )
        self.comissao = ComissaoVendedor.objects.create(
            fechamento=self.fechamento, vendedor=self.vendedor,
            vendedor_uuid_original=self.vendedor.uuid, vendedor_nome_original="Vendedor F24",
            total_vendas_vendedor=Decimal("5000.00"), elegivel=True, valor_comissao=Decimal("100.00"),
        )

    @patch("financeiro.services.criar_titulo_financeiro")
    def test_delega_snapshot_para_financeiro_com_dados_estaveis(self, criar):
        plano = object()
        criar.return_value = object()
        retorno = gerar_titulo_financeiro_comissao(
            comissao=self.comissao, vencimento=date(2026,10,10)
        )
        self.assertIs(retorno, criar.return_value)
        kw = criar.call_args.kwargs
        self.assertEqual(kw["matriz"], self.matriz)
        self.assertEqual(kw["loja"], self.loja)
        self.assertEqual(kw["natureza"], TituloFinanceiro.Natureza.PAGAR)
        self.assertEqual(kw["origem_tipo"], TituloFinanceiro.OrigemTipo.COMISSAO)
        self.assertEqual(kw["origem_id"], str(self.comissao.pk))
        self.assertEqual(kw["chave_idempotencia"], f"COMISSAO:{self.comissao.pk}")
        self.assertEqual(kw["parcelas"][0]["valor"], Decimal("100.00"))
        self.assertEqual(kw["parcelas"][0]["vencimento"], date(2026,10,10))

    def test_rejeita_snapshot_sem_valor_positivo(self):
        zero = ComissaoVendedor.objects.create(
            fechamento=FechamentoComissao.objects.create(
                matriz=self.matriz, loja=Loja.objects.create(matriz=self.matriz,nome="Loja Zero"),
                competencia_ano=2026, competencia_mes=8, total_vendas_loja=Decimal("0.00"),
                percentual_aplicado=Decimal("0.0000"),
            ),
            vendedor=self.vendedor, vendedor_uuid_original=self.vendedor.uuid,
            vendedor_nome_original="Vendedor Zero", total_vendas_vendedor=Decimal("0.00"),
            elegivel=True, valor_comissao=Decimal("0.00"),
        )
        with self.assertRaises(ValidationError):
            gerar_titulo_financeiro_comissao(
                comissao=zero, vencimento=date(2026,9,10)
            )