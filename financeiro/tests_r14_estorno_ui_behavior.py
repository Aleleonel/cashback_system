import uuid
from datetime import date
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from accounts.models import PermissaoUsuario, Usuario
from accounts.permissions import PERMISSAO_FINANCEIRO_BAIXAR
from empresas.models import Loja, Matriz
from financeiro.models import BaixaFinanceira, ContaFinanceira, TituloFinanceiro
from financeiro.services import (
    criar_titulo_financeiro,
    registrar_baixa_financeira_com_caixa,
)
from pdv.choices import TipoFormaPagamento, TipoMovimentacaoCaixa
from pdv.models import Caixa, FormaPagamento, MovimentacaoCaixa, SessaoCaixa
from pdv.services.vendas.caixa import calcular_saldo_sessao_caixa


class R14EstornoUIBehaviorTests(TestCase):
    def setUp(self):
        self.matriz = Matriz.objects.create(nome="Matriz R14H2", cnpj="93939393000193")
        self.loja = Loja.objects.create(matriz=self.matriz, nome="Loja R14H2")
        self.operador = Usuario.objects.create_user(
            username="r14h2_operador",
            password="SenhaTeste123!",
            matriz=self.matriz,
            perfil=Usuario.PERFIL_OPERADOR,
        )
        self.operador.lojas.add(self.loja)
        PermissaoUsuario.objects.create(
            usuario=self.operador,
            permissao=PERMISSAO_FINANCEIRO_BAIXAR,
        )

        self.pix = FormaPagamento.objects.create(
            matriz=self.matriz,
            nome="PIX R14H2",
            codigo="PIX_R14H2",
            tipo=TipoFormaPagamento.PIX,
            movimenta_caixa=False,
            ativa=True,
        )
        self.dinheiro = FormaPagamento.objects.create(
            matriz=self.matriz,
            nome="Dinheiro R14H2",
            codigo="DIN_R14H2",
            tipo=TipoFormaPagamento.DINHEIRO,
            movimenta_caixa=True,
            ativa=True,
        )
        self.conta = ContaFinanceira.objects.create(
            matriz=self.matriz,
            loja=self.loja,
            tipo="BANCO",
            nome="Conta PIX R14H2",
            agencia="",
            numero="",
            digito="",
            chave_pix="pix-r14h2",
            ativo=True,
        )

    def criar_titulo(self, chave, valor="40.00"):
        titulo = criar_titulo_financeiro(
            matriz=self.matriz,
            loja=self.loja,
            natureza=TituloFinanceiro.Natureza.PAGAR,
            origem_tipo=TituloFinanceiro.OrigemTipo.MANUAL,
            origem_id=chave,
            chave_idempotencia=chave,
            descricao=chave,
            data_emissao=date.today(),
            parcelas=[{
                "numero": 1,
                "vencimento": date.today(),
                "valor": Decimal(valor),
            }],
        )
        return titulo, titulo.parcelas.get()

    def criar_baixa_pix(self, parcela, valor="40.00", chave=None):
        return registrar_baixa_financeira_com_caixa(
            parcela=parcela,
            valor=Decimal(valor),
            data=date.today(),
            chave_idempotencia=chave or ("bx-" + str(uuid.uuid4())),
            forma_pagamento=self.pix,
            conta_financeira=self.conta,
            observacao="Baixa PIX R14H2",
        )

    def url(self, titulo, baixa):
        return reverse(
            "financeiro:baixa_estornar",
            kwargs={"titulo_uuid": titulo.uuid, "parcela_id": baixa.parcela_id, "baixa_id": baixa.pk},
        )

    def test_get_formulario_estorno_responde_200_com_token_data_e_valor(self):
        titulo, parcela = self.criar_titulo("r14h2-get")
        baixa = self.criar_baixa_pix(parcela)
        self.client.force_login(self.operador)

        response = self.client.get(self.url(titulo, baixa))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Estornar baixa")
        self.assertContains(response, 'name="chave_idempotencia"')
        self.assertEqual(response.context["form"].initial["valor"], Decimal("40.00"))
        self.assertEqual(response.context["form"].initial["data"], date.today())

    def test_post_pix_cria_estorno_preserva_forma_conta_e_nao_movimenta_caixa(self):
        titulo, parcela = self.criar_titulo("r14h2-pix")
        baixa = self.criar_baixa_pix(parcela)
        self.client.force_login(self.operador)

        response = self.client.get(self.url(titulo, baixa))
        token = response.context["chave_idempotencia"]
        response = self.client.post(self.url(titulo, baixa), {
            "valor": "40.00",
            "data": date.today().isoformat(),
            "observacao": "Estorno PIX R14H2",
            "chave_idempotencia": token,
        })

        self.assertEqual(response.status_code, 302)
        estorno = parcela.baixas.get(tipo=BaixaFinanceira.Tipo.ESTORNO)
        self.assertEqual(estorno.valor, Decimal("40.00"))
        self.assertEqual(estorno.forma_pagamento_id, self.pix.pk)
        self.assertEqual(estorno.conta_financeira_id, self.conta.pk)
        self.assertIsNone(estorno.sessao_caixa_id)
        self.assertIsNone(estorno.movimentacao_caixa_id)
        self.assertEqual(MovimentacaoCaixa.objects.count(), 0)

    def test_sem_permissao_baixar_estorno_e_bloqueado(self):
        titulo, parcela = self.criar_titulo("r14h2-permissao")
        baixa = self.criar_baixa_pix(parcela)
        PermissaoUsuario.objects.filter(
            usuario=self.operador,
            permissao=PERMISSAO_FINANCEIRO_BAIXAR,
        ).delete()
        self.client.force_login(self.operador)

        response = self.client.get(self.url(titulo, baixa))

        self.assertIn(response.status_code, (403, 404))
        self.assertEqual(
            parcela.baixas.filter(tipo=BaixaFinanceira.Tipo.ESTORNO).count(), 0
        )

    def test_loja_nao_autorizada_retorna_404_sem_estorno(self):
        titulo, parcela = self.criar_titulo("r14h2-escopo")
        baixa = self.criar_baixa_pix(parcela)
        self.operador.lojas.remove(self.loja)
        self.client.force_login(self.operador)

        response = self.client.get(self.url(titulo, baixa))

        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            parcela.baixas.filter(tipo=BaixaFinanceira.Tipo.ESTORNO).count(), 0
        )

    def test_retry_mesmo_token_nao_duplica_estorno_pix(self):
        titulo, parcela = self.criar_titulo("r14h2-idem")
        baixa = self.criar_baixa_pix(parcela)
        self.client.force_login(self.operador)
        response = self.client.get(self.url(titulo, baixa))
        token = response.context["chave_idempotencia"]
        payload = {
            "valor": "40.00",
            "data": date.today().isoformat(),
            "observacao": "Retry R14H2",
            "chave_idempotencia": token,
        }

        primeira = self.client.post(self.url(titulo, baixa), payload)
        segunda = self.client.post(self.url(titulo, baixa), payload)

        self.assertEqual(primeira.status_code, 302)
        self.assertEqual(segunda.status_code, 302)
        self.assertEqual(
            parcela.baixas.filter(tipo=BaixaFinanceira.Tipo.ESTORNO).count(), 1
        )

    def test_post_dinheiro_cria_estorno_de_caixa_referenciando_movimento_original(self):
        titulo, parcela = self.criar_titulo("r14h2-dinheiro", "15.00")
        caixa = Caixa.objects.create(
            matriz=self.matriz,
            loja=self.loja,
            nome="Caixa R14H2",
            codigo="R14H2",
        )
        sessao = SessaoCaixa.objects.create(
            caixa=caixa,
            operador_abertura=self.operador,
            valor_abertura=Decimal("100.00"),
        )
        MovimentacaoCaixa.objects.create(
            sessao_caixa=sessao,
            tipo=TipoMovimentacaoCaixa.ABERTURA,
            valor=Decimal("100.00"),
            operador=self.operador,
            descricao="Abertura R14H2",
        )
        baixa = registrar_baixa_financeira_com_caixa(
            parcela=parcela,
            valor=Decimal("15.00"),
            data=date.today(),
            chave_idempotencia="bx-r14h2-dinheiro",
            forma_pagamento=self.dinheiro,
            sessao_caixa=sessao,
            operador=self.operador,
        )
        movimento_original_id = baixa.movimentacao_caixa_id
        self.assertEqual(calcular_saldo_sessao_caixa(sessao=sessao), Decimal("85.00"))
        self.client.force_login(self.operador)

        get_response = self.client.get(self.url(titulo, baixa))
        token = get_response.context["chave_idempotencia"]
        response = self.client.post(self.url(titulo, baixa), {
            "valor": "15.00",
            "data": date.today().isoformat(),
            "observacao": "Estorno dinheiro R14H2",
            "chave_idempotencia": token,
        })

        self.assertEqual(response.status_code, 302)
        estorno = parcela.baixas.get(tipo=BaixaFinanceira.Tipo.ESTORNO)
        self.assertEqual(estorno.forma_pagamento_id, self.dinheiro.pk)
        self.assertEqual(estorno.sessao_caixa_id, sessao.pk)
        self.assertIsNotNone(estorno.movimentacao_caixa_id)
        self.assertEqual(estorno.movimentacao_caixa.tipo, TipoMovimentacaoCaixa.ESTORNO)
        self.assertEqual(
            estorno.movimentacao_caixa.movimentacao_estornada_id,
            movimento_original_id,
        )
        self.assertEqual(calcular_saldo_sessao_caixa(sessao=sessao), Decimal("100.00"))

    def test_estorno_parcial_da_primeira_de_duas_baixas_limita_se_a_baixa_especifica(self):
        titulo, parcela = self.criar_titulo("r14h2-multiplas", "100.00")
        baixa1 = self.criar_baixa_pix(parcela, "30.00", "bx-r14h2-multi-1")
        self.criar_baixa_pix(parcela, "20.00", "bx-r14h2-multi-2")
        self.client.force_login(self.operador)

        get_response = self.client.get(self.url(titulo, baixa1))
        self.assertEqual(get_response.status_code, 200)
        self.assertEqual(get_response.context["form"].initial["valor"], Decimal("30.00"))
        token = get_response.context["chave_idempotencia"]

        primeira = self.client.post(self.url(titulo, baixa1), {
            "valor": "10.00",
            "data": date.today().isoformat(),
            "observacao": "Parcial baixa 1",
            "chave_idempotencia": token,
        })
        self.assertEqual(primeira.status_code, 302)

        segundo_get = self.client.get(self.url(titulo, baixa1))
        self.assertEqual(segundo_get.status_code, 200)
        self.assertEqual(
            segundo_get.context["form"].initial["valor"],
            Decimal("20.00"),
        )