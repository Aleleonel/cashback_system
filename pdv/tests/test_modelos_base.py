from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from empresas.models import Loja, Matriz
from pdv.choices import (
    StatusOperacaoVenda,
    TipoFormaPagamento,
    TipoMovimentacaoCaixa,
)
from pdv.models import (
    Caixa,
    FormaPagamento,
    MovimentacaoCaixa,
    PagamentoVenda,
    SessaoCaixa,
    Venda,
)
from pdv.services import obter_ou_criar_cliente_consumidor


class ModelosBasePDVTests(TestCase):
    def setUp(self):
        self.matriz = Matriz.objects.create(nome="Matriz Teste")
        self.loja = Loja.objects.create(
            matriz=self.matriz,
            nome="Loja Teste",
            cnpj="00.000.000/0001-00",
        )
        self.usuario = get_user_model().objects.create_user(
            username="operador",
            password="senha-teste",
            matriz=self.matriz,
        )
        self.usuario.lojas.add(self.loja)

        self.caixa = Caixa.objects.create(
            matriz=self.matriz,
            loja=self.loja,
            nome="Caixa Principal",
            codigo="CX01",
        )

    def test_cliente_consumidor_e_unico_por_matriz(self):
        primeiro = obter_ou_criar_cliente_consumidor(
            matriz=self.matriz,
            loja=self.loja,
        )
        segundo = obter_ou_criar_cliente_consumidor(
            matriz=self.matriz,
            loja=self.loja,
        )

        self.assertEqual(primeiro.pk, segundo.pk)
        self.assertEqual(primeiro.nome, "CONSUMIDOR")
        self.assertEqual(primeiro.cpf, "CONSUMIDOR")

    def test_nao_permite_duas_sessoes_abertas_no_mesmo_caixa(self):
        SessaoCaixa.objects.create(
            caixa=self.caixa,
            operador_abertura=self.usuario,
            valor_abertura=Decimal("100.00"),
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                SessaoCaixa.objects.create(
                    caixa=self.caixa,
                    operador_abertura=self.usuario,
                    valor_abertura=Decimal("50.00"),
                )

    def test_forma_crediario_funcionario_customizada(self):
        forma = FormaPagamento(
            matriz=self.matriz,
            nome="Crediario Funcionario",
            codigo="CRED_FUNC",
            tipo=TipoFormaPagamento.CREDIARIO,
            ativa=True,
            permite_parcelamento=True,
            maximo_parcelas=6,
            exige_cliente_identificado=True,
            exige_autorizacao=True,
            gera_contas_receber=True,
            movimenta_caixa=False,
            somente_funcionario=True,
        )
        forma.full_clean()
        forma.save()

        self.assertTrue(forma.somente_funcionario)
        self.assertTrue(forma.gera_contas_receber)
        self.assertFalse(forma.movimenta_caixa)

    def test_venda_finalizada_exige_cliente_e_sessao(self):
        venda = Venda(
            matriz=self.matriz,
            loja=self.loja,
            operador=self.usuario,
            status=StatusOperacaoVenda.FINALIZADA,
            subtotal=Decimal("100.00"),
            desconto=Decimal("0.00"),
            acrescimo=Decimal("0.00"),
            total=Decimal("100.00"),
        )

        with self.assertRaises(ValidationError):
            venda.full_clean()

    def test_crediario_nao_aceita_cliente_consumidor(self):
        consumidor = obter_ou_criar_cliente_consumidor(
            matriz=self.matriz,
            loja=self.loja,
        )
        sessao = SessaoCaixa.objects.create(
            caixa=self.caixa,
            operador_abertura=self.usuario,
            valor_abertura=Decimal("0.00"),
        )
        venda = Venda.objects.create(
            matriz=self.matriz,
            loja=self.loja,
            sessao_caixa=sessao,
            cliente=consumidor,
            operador=self.usuario,
            subtotal=Decimal("100.00"),
            total=Decimal("100.00"),
        )
        forma = FormaPagamento.objects.create(
            matriz=self.matriz,
            nome="Crediario Funcionario",
            codigo="CRED_FUNC",
            tipo=TipoFormaPagamento.CREDIARIO,
            permite_parcelamento=True,
            maximo_parcelas=6,
            exige_cliente_identificado=True,
            exige_autorizacao=True,
            gera_contas_receber=True,
            movimenta_caixa=False,
            somente_funcionario=True,
        )
        pagamento = PagamentoVenda(
            venda=venda,
            forma_pagamento=forma,
            valor=Decimal("100.00"),
            parcelas=2,
            autorizado_por=self.usuario,
        )

        with self.assertRaises(ValidationError):
            pagamento.full_clean()

    def test_movimentacao_caixa_e_imutavel(self):
        sessao = SessaoCaixa.objects.create(
            caixa=self.caixa,
            operador_abertura=self.usuario,
            valor_abertura=Decimal("100.00"),
        )
        movimento = MovimentacaoCaixa.objects.create(
            sessao_caixa=sessao,
            tipo=TipoMovimentacaoCaixa.ABERTURA,
            valor=Decimal("100.00"),
            operador=self.usuario,
        )
        movimento.descricao = "Tentativa de alterar"

        with self.assertRaises(ValidationError):
            movimento.save()

        with self.assertRaises(ValidationError):
            movimento.delete()
