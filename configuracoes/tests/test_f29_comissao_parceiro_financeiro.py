from datetime import timedelta, date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from configuracoes.services_comissoes import gerar_titulo_financeiro_comissao_parceiro
from financeiro.models import TituloFinanceiro
from empresas.models import Loja, Matriz
from clientes.models import Cliente
from vouchers.models import ComissaoParceiro, Parceiro, UsoVoucher, Voucher


class F29ComissaoParceiroFinanceiroTest(TestCase):
    def setUp(self):
        self.matriz = Matriz.objects.create(nome="Matriz F29")
        self.loja = Loja.objects.create(matriz=self.matriz, nome="Loja F29")
        User = get_user_model()
        self.usuario = User.objects.create_user(username="f29user", password="teste-f29")
        self.cliente = Cliente.objects.create(matriz=self.matriz, loja_cadastro=self.loja, nome="Cliente F29")

        self.parceiro = Parceiro.objects.create(
            matriz=self.matriz,
            nome="Parceiro F29",
            tipo_comissao=Parceiro.TipoComissao.PERCENTUAL,
            percentual_comissao=Decimal("10.0000"),
            base_calculo=Parceiro.BaseCalculo.APOS_DESCONTO,
            ativo=True,
        )
        hoje = timezone.localdate()
        self.voucher = Voucher.objects.create(
            matriz=self.matriz,
            codigo="F29PARC",
            nome="Voucher F29 Parceiro",
            tipo=Voucher.Tipo.VALOR_FIXO,
            valor=Decimal("10.00"),
            percentual=None,
            data_inicio=hoje,
            data_fim=hoje + timedelta(days=30),
            limite_utilizacao=20,
            total_utilizado=0,
            parceiro=self.parceiro,
        )
        self.uso = UsoVoucher.objects.create(
            matriz=self.matriz,
            voucher=self.voucher,
            cliente=self.cliente,
            loja=self.loja,
            usuario=self.usuario,
            parceiro=self.parceiro,
            valor_compra=Decimal("100.00"),
            valor_desconto=Decimal("10.00"),
        )
        self.comissao = ComissaoParceiro.objects.create(
            uso_voucher=self.uso,
            matriz=self.matriz,
            parceiro=self.parceiro,
            tipo_comissao=Parceiro.TipoComissao.PERCENTUAL,
            base_calculo=Parceiro.BaseCalculo.APOS_DESCONTO,
            valor_base=Decimal("90.00"),
            percentual_aplicado=Decimal("10.0000"),
            valor_comissao=Decimal("9.00"),
        )

    def test_provisiona_real_com_namespace_proprio_sem_loja_e_idempotencia(self):
        vencimento = date(2026, 11, 10)
        titulo = gerar_titulo_financeiro_comissao_parceiro(
            comissao=self.comissao, vencimento=vencimento
        )
        self.assertIsInstance(titulo, TituloFinanceiro)
        self.assertEqual(titulo.matriz, self.matriz)
        self.assertIsNone(titulo.loja)
        self.assertEqual(titulo.natureza, TituloFinanceiro.Natureza.PAGAR)
        self.assertEqual(titulo.origem_tipo, TituloFinanceiro.OrigemTipo.COMISSAO)
        self.assertEqual(titulo.origem_id, f"PARCEIRO:{self.comissao.pk}")
        self.assertEqual(titulo.chave_idempotencia, f"COMISSAO_PARCEIRO:{self.comissao.pk}")
        self.assertEqual(titulo.valor_original, Decimal("9.00"))
        self.assertEqual(titulo.data_emissao, self.comissao.criado_em.date())
        parcela = titulo.parcelas.get()
        self.assertEqual(parcela.numero, 1)
        self.assertEqual(parcela.vencimento, vencimento)
        self.assertEqual(parcela.valor_original, Decimal("9.00"))
        repetido = gerar_titulo_financeiro_comissao_parceiro(
            comissao=self.comissao, vencimento=vencimento
        )
        self.assertEqual(repetido.pk, titulo.pk)
        self.assertEqual(
            TituloFinanceiro.objects.filter(
                matriz=self.matriz,
                chave_idempotencia=f"COMISSAO_PARCEIRO:{self.comissao.pk}",
            ).count(), 1
        )
    def test_rejeita_objeto_invalido(self):
        with self.assertRaises(ValueError):
            gerar_titulo_financeiro_comissao_parceiro(
                comissao=self.parceiro, vencimento=date(2026, 11, 10)
            )