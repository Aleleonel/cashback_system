import uuid

from datetime import date
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from accounts.models import PermissaoUsuario, Usuario
from accounts.permissions import PERMISSAO_FINANCEIRO_BAIXAR
from empresas.models import Loja, Matriz
from financeiro.models import BaixaFinanceira, TituloFinanceiro
from financeiro.services import criar_titulo_financeiro
from pdv.choices import TipoFormaPagamento, TipoMovimentacaoCaixa
from pdv.models import Caixa, FormaPagamento, MovimentacaoCaixa, SessaoCaixa
from pdv.services.vendas.caixa import calcular_saldo_sessao_caixa


class BaixaDinheiroUiBehaviorR9KUXTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.matriz = Matriz.objects.create(nome="Matriz R9KUX14F", cnpj="94949494000194")
        cls.loja = Loja.objects.create(matriz=cls.matriz, nome="Loja R9KUX14F")
        cls.operador = Usuario.objects.create_user(
            username="r9kux14f_operador", password="SenhaTeste123!",
            matriz=cls.matriz, perfil=Usuario.PERFIL_OPERADOR,
        )
        cls.operador.lojas.add(cls.loja)
        PermissaoUsuario.objects.create(
            usuario=cls.operador, permissao=PERMISSAO_FINANCEIRO_BAIXAR,
        )
        cls.dinheiro = FormaPagamento.objects.create(
            matriz=cls.matriz, nome="Dinheiro R9KUX14F", codigo="DIN_R9KUX14F",
            tipo=TipoFormaPagamento.DINHEIRO, movimenta_caixa=True, ativa=True,
        )
        cls.titulo = criar_titulo_financeiro(
            matriz=cls.matriz, loja=cls.loja,
            natureza=TituloFinanceiro.Natureza.PAGAR,
            origem_tipo=TituloFinanceiro.OrigemTipo.MANUAL,
            origem_id="r9kux14f", chave_idempotencia="r9kux14f",
            descricao="Motoboy teste UI", data_emissao=date.today(),
            parcelas=[{"numero": 1, "vencimento": date.today(), "valor": Decimal("15.00")}],
        )
        cls.parcela = cls.titulo.parcelas.get()
        cls.caixa = Caixa.objects.create(matriz=cls.matriz, loja=cls.loja, nome="Caixa R9KUX14G2", codigo="R9KUX14G2")
        cls.sessao = SessaoCaixa.objects.create(caixa=cls.caixa, operador_abertura=cls.operador, valor_abertura=Decimal("100.00"))
        MovimentacaoCaixa.objects.create(sessao_caixa=cls.sessao, tipo=TipoMovimentacaoCaixa.ABERTURA, valor=Decimal("100.00"), operador=cls.operador, descricao="Abertura")

    def test_get_baixa_dinheiro_com_forma_ativa_responde_200(self):
        self.client.force_login(self.operador)
        response = self.client.get(reverse(
            "financeiro:parcela_baixa_nova",
            kwargs={"titulo_uuid": self.titulo.uuid, "parcela_id": self.parcela.pk},
        ))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Registrar baixa em dinheiro")
    def test_post_pagar_dinheiro_cria_baixa_sangria_e_liquida(self):
        self.client.force_login(self.operador)
        response = self.client.post(
            reverse(
                "financeiro:parcela_baixa_nova",
                kwargs={"titulo_uuid": self.titulo.uuid, "parcela_id": self.parcela.pk},
            ),
            {"valor": "15.00", "data": date.today().isoformat(), "observacao": "Motoboy teste POST", "chave_idempotencia": str(uuid.uuid4())},
        )
        self.assertEqual(response.status_code, 302)
        self.parcela.refresh_from_db()
        self.titulo.refresh_from_db()
        baixa = self.parcela.baixas.get(tipo=BaixaFinanceira.Tipo.BAIXA)
        self.assertEqual(baixa.valor, Decimal("15.00"))
        self.assertEqual(baixa.forma_pagamento_id, self.dinheiro.pk)
        self.assertEqual(baixa.sessao_caixa_id, self.sessao.pk)
        self.assertIsNotNone(baixa.movimentacao_caixa_id)
        self.assertEqual(baixa.movimentacao_caixa.tipo, TipoMovimentacaoCaixa.SANGRIA)
        self.assertEqual(baixa.movimentacao_caixa.valor, Decimal("15.00"))
        self.assertEqual(self.parcela.status, self.parcela.Status.LIQUIDADO)
        self.assertEqual(self.titulo.status, TituloFinanceiro.Status.LIQUIDADO)
        self.assertEqual(calcular_saldo_sessao_caixa(sessao=self.sessao), Decimal("85.00"))
    def test_post_sem_sessao_propria_nao_cria_baixa(self):
        MovimentacaoCaixa.objects.filter(sessao_caixa=self.sessao).delete()
        self.sessao.delete()
        self.client.force_login(self.operador)
        response = self.client.post(
            reverse(
                "financeiro:parcela_baixa_nova",
                kwargs={"titulo_uuid": self.titulo.uuid, "parcela_id": self.parcela.pk},
            ),
            {"valor": "15.00", "data": date.today().isoformat(), "observacao": "Sem sessao", "chave_idempotencia": str(uuid.uuid4())},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Nao existe sessao de caixa aberta por este usuario nesta loja.")
        self.assertFalse(self.parcela.baixas.exists())
        self.parcela.refresh_from_db()
        self.titulo.refresh_from_db()
        self.assertEqual(self.parcela.status, self.parcela.Status.ABERTO)
        self.assertEqual(self.titulo.status, TituloFinanceiro.Status.ABERTO)
    def test_baixa_loja_nao_autorizada_retorna_404(self):
        self.operador.lojas.remove(self.loja)
        self.client.force_login(self.operador)
        response = self.client.get(
            reverse(
                "financeiro:parcela_baixa_nova",
                kwargs={"titulo_uuid": self.titulo.uuid, "parcela_id": self.parcela.pk},
            )
        )
        self.assertEqual(response.status_code, 404)
        self.assertFalse(self.parcela.baixas.exists())
    def test_baixa_sem_permissao_gerenciar_e_bloqueada(self):
        PermissaoUsuario.objects.filter(
            usuario=self.operador, permissao=PERMISSAO_FINANCEIRO_BAIXAR
        ).delete()
        self.client.force_login(self.operador)
        response = self.client.get(
            reverse(
                "financeiro:parcela_baixa_nova",
                kwargs={"titulo_uuid": self.titulo.uuid, "parcela_id": self.parcela.pk},
            )
        )
        self.assertIn(response.status_code, (403, 404))
        self.assertFalse(self.parcela.baixas.exists())
    def test_post_valor_acima_saldo_exibe_erro_sem_500(self):
        self.client.force_login(self.operador)
        response = self.client.post(
            reverse(
                "financeiro:parcela_baixa_nova",
                kwargs={"titulo_uuid": self.titulo.uuid, "parcela_id": self.parcela.pk},
            ),
            {"valor": "16.00", "data": date.today().isoformat(), "observacao": "Acima do saldo", "chave_idempotencia": str(uuid.uuid4())},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "A baixa nao pode exceder o saldo da parcela.")
        self.assertFalse(self.parcela.baixas.exists())
        self.assertFalse(
            MovimentacaoCaixa.objects.filter(
                sessao_caixa=self.sessao, tipo=TipoMovimentacaoCaixa.SANGRIA
            ).exists()
        )
    def test_multiplas_formas_dinheiro_ativas_nao_geram_500(self):
        FormaPagamento.objects.create(
            matriz=self.matriz,
            nome="Dinheiro duplicado R9KUX14I2",
            codigo="DINHEIRO-R9KUX14I2",
            tipo=TipoFormaPagamento.DINHEIRO,
            ativa=True,
        )
        self.client.force_login(self.operador)
        response = self.client.get(
            reverse(
                "financeiro:parcela_baixa_nova",
                kwargs={"titulo_uuid": self.titulo.uuid, "parcela_id": self.parcela.pk},
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "Existe mais de uma forma de pagamento Dinheiro ativa. Revise a configuracao.",
        )
        self.assertFalse(self.parcela.baixas.exists())
    def test_get_fornece_token_idempotencia_e_retry_nao_duplica(self):
        self.client.force_login(self.operador)
        url = reverse(
            "financeiro:parcela_baixa_nova",
            kwargs={"titulo_uuid": self.titulo.uuid, "parcela_id": self.parcela.pk},
        )
        get_response = self.client.get(url)
        self.assertEqual(get_response.status_code, 200)
        self.assertContains(get_response, 'name="chave_idempotencia"')
        token = get_response.context["chave_idempotencia"]

        payload = {
            "valor": "15.00",
            "data": date.today().isoformat(),
            "observacao": "Retry idempotente",
            "chave_idempotencia": token,
        }
        primeira = self.client.post(url, payload)
        segunda = self.client.post(url, payload)

        self.assertEqual(primeira.status_code, 302)
        self.assertEqual(segunda.status_code, 302)
        self.assertEqual(
            self.parcela.baixas.filter(tipo=BaixaFinanceira.Tipo.BAIXA).count(), 1
        )
        self.assertEqual(
            MovimentacaoCaixa.objects.filter(
                sessao_caixa=self.sessao, tipo=TipoMovimentacaoCaixa.SANGRIA
            ).count(),
            1,
        )
