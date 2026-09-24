from datetime import datetime
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from empresas.models import Matriz, Loja
from financeiro.models import TituloFinanceiro
from pdv.choices import TipoFormaPagamento
from pdv.models import FormaPagamento, PagamentoVenda, Venda
from pdv.services.vendas.finalizacao import gerar_contas_receber_venda


class R20VendaContasReceberBehaviorTests(TestCase):
    def setUp(self):
        self.matriz = Matriz.objects.create(nome="Matriz R20E2")
        self.loja = Loja.objects.create(matriz=self.matriz, nome="Loja R20E2")
        self.operador = get_user_model().objects.create_user(
            username="operador_r20e2",
            password="senha-teste",
            matriz=self.matriz,
        )
        self.operador.lojas.add(self.loja)
        self.venda = Venda.objects.create(
            matriz=self.matriz,
            loja=self.loja,
            operador=self.operador,
            total=Decimal("0.00"),
        )
        self.venda.finalizada_em = timezone.make_aware(datetime(2026, 1, 31, 12, 0, 0))
        self.venda.save(update_fields=["finalizada_em"])

        self.crediario = FormaPagamento.objects.create(
            matriz=self.matriz,
            nome="Crediario R20E2",
            codigo="CRED-R20E2",
            tipo=TipoFormaPagamento.OUTRO,
            permite_parcelamento=True,
            maximo_parcelas=12,
            exige_cliente_identificado=False,
            gera_contas_receber=True,
            movimenta_caixa=False,
        )
        self.pix = FormaPagamento.objects.create(
            matriz=self.matriz,
            nome="PIX R20E2",
            codigo="PIX-R20E2",
            tipo=TipoFormaPagamento.PIX,
            permite_parcelamento=False,
            maximo_parcelas=1,
            exige_cliente_identificado=False,
            gera_contas_receber=False,
            movimenta_caixa=True,
        )

    def _pagamento(self, forma, valor, parcelas=1):
        return PagamentoVenda.objects.create(
            venda=self.venda,
            forma_pagamento=forma,
            valor=Decimal(valor),
            parcelas=parcelas,
        )

    def test_pagamento_elegivel_cria_um_titulo_receber_com_parcelas_exatas(self):
        pagamento = self._pagamento(self.crediario, "100.00", 3)

        titulos = gerar_contas_receber_venda(venda=self.venda)
        self.assertEqual(len(titulos), 1)

        titulo = TituloFinanceiro.objects.get(
            origem_tipo=TituloFinanceiro.OrigemTipo.VENDA_PAGAMENTO,
            origem_id=str(pagamento.uuid),
        )
        self.assertEqual(titulo.natureza, TituloFinanceiro.Natureza.RECEBER)
        self.assertEqual(titulo.matriz, self.matriz)
        self.assertEqual(titulo.loja, self.loja)
        self.assertEqual(titulo.valor_original, Decimal("100.00"))

        parcelas = list(titulo.parcelas.order_by("numero"))
        self.assertEqual([p.valor_original for p in parcelas], [
            Decimal("33.34"), Decimal("33.33"), Decimal("33.33")
        ])
        self.assertEqual([str(p.vencimento) for p in parcelas], [
            "2026-02-28", "2026-03-28", "2026-04-28"
        ])

    def test_pagamento_nao_elegivel_nao_cria_titulo(self):
        self._pagamento(self.pix, "50.00", 1)
        titulos = gerar_contas_receber_venda(venda=self.venda)
        self.assertEqual(titulos, [])
        self.assertFalse(TituloFinanceiro.objects.exists())

    def test_pagamentos_mistos_criam_titulo_apenas_para_elegivel(self):
        elegivel = self._pagamento(self.crediario, "40.00", 2)
        self._pagamento(self.pix, "60.00", 1)

        gerar_contas_receber_venda(venda=self.venda)

        self.assertEqual(TituloFinanceiro.objects.count(), 1)
        titulo = TituloFinanceiro.objects.get()
        self.assertEqual(titulo.origem_id, str(elegivel.uuid))
        self.assertEqual(titulo.valor_original, Decimal("40.00"))

    def test_dois_pagamentos_elegiveis_criam_dois_titulos_independentes(self):
        p1 = self._pagamento(self.crediario, "30.00", 2)
        p2 = self._pagamento(self.crediario, "70.00", 4)

        gerar_contas_receber_venda(venda=self.venda)

        titulos = TituloFinanceiro.objects.order_by("origem_id")
        self.assertEqual(titulos.count(), 2)
        self.assertEqual(
            set(titulos.values_list("origem_id", flat=True)),
            {str(p1.uuid), str(p2.uuid)},
        )
        self.assertEqual(
            sorted(t.parcelas.count() for t in titulos),
            [2, 4],
        )

    def test_reprocessamento_e_idempotente(self):
        self._pagamento(self.crediario, "10.01", 3)

        gerar_contas_receber_venda(venda=self.venda)
        gerar_contas_receber_venda(venda=self.venda)

        self.assertEqual(TituloFinanceiro.objects.count(), 1)
        titulo = TituloFinanceiro.objects.get()
        self.assertEqual(titulo.parcelas.count(), 3)
        self.assertEqual(
            sum((p.valor_original for p in titulo.parcelas.all()), Decimal("0.00")),
            Decimal("10.01"),
        )

    def test_falha_financeira_propaga_excecao(self):
        self._pagamento(self.crediario, "25.00", 1)
        with patch(
            "pdv.services.vendas.finalizacao.criar_titulo_financeiro",
            side_effect=RuntimeError("falha financeira controlada"),
        ):
            with self.assertRaisesRegex(RuntimeError, "falha financeira controlada"):
                gerar_contas_receber_venda(venda=self.venda)
