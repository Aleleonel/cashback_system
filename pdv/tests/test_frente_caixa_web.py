import json
import uuid
from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from cashback.models import LancamentoCashback
from clientes.models import Cliente
from core.models import ConfiguracaoSistema
from empresas.models import Loja, Matriz
from pdv.choices import StatusOperacaoVenda
from pdv.models import Caixa, SessaoCaixa, Venda
from produtos.choices import StatusProduto
from produtos.models import Produto, UnidadeMedida
from vouchers.models import Voucher


class FrenteCaixaWebTests(TestCase):
    def setUp(self):
        self.matriz = Matriz.objects.create(nome="Matriz PDV Web")
        self.loja = Loja.objects.create(
            matriz=self.matriz,
            nome="Loja PDV Web",
            cnpj="11.111.111/0001-11",
        )
        self.usuario = get_user_model().objects.create_user(
            username="operador_web",
            password="senha-teste",
            matriz=self.matriz,
        )
        self.usuario.lojas.add(self.loja)
        self.caixa = Caixa.objects.create(
            matriz=self.matriz,
            loja=self.loja,
            nome="Caixa Web",
            codigo="CXWEB",
        )
        self.sessao = SessaoCaixa.objects.create(
            caixa=self.caixa,
            operador_abertura=self.usuario,
            valor_abertura=Decimal("0.00"),
        )
        unidade_fields = {
            field.name
            for field in UnidadeMedida._meta.get_fields()
            if getattr(field, "concrete", False)
        }
        unidade_kwargs = {
            "matriz": self.matriz,
            "sigla": "UN",
        }

        if "descricao" in unidade_fields:
            unidade_kwargs["descricao"] = "Unidade"
        elif "nome" in unidade_fields:
            unidade_kwargs["nome"] = "Unidade"
        elif "titulo" in unidade_fields:
            unidade_kwargs["titulo"] = "Unidade"

        if "codigo" in unidade_fields:
            unidade_kwargs["codigo"] = "UN"

        self.unidade = UnidadeMedida.objects.create(**unidade_kwargs)
        self.produto = Produto.objects.create(
            matriz=self.matriz,
            unidade_medida=self.unidade,
            codigo_interno="PDV-WEB-001",
            nome="Produto Frente Caixa",
            custo_base=Decimal("10.00"),
            preco_venda=Decimal("20.00"),
            controla_estoque=False,
            status=StatusProduto.ATIVO,
        )
        self.vendedor = get_user_model().objects.create_user(
            username="vendedor_web",
            first_name="Vendedor",
            last_name="Teste",
            password="senha-teste",
            matriz=self.matriz,
        )
        self.vendedor.lojas.add(self.loja)
        self.cliente_pdv = Cliente.objects.create(
            matriz=self.matriz,
            loja_cadastro=self.loja,
            nome="Cliente Frente Caixa",
            cpf="222.222.222-22",
            telefone="(11) 99999-2222",
            email="cliente.pdv@example.com",
        )
        self.configuracao = ConfiguracaoSistema.objects.create(
            matriz=self.matriz,
            percentual_cashback=Decimal("5.00"),
            valor_minimo_compra=Decimal("0.00"),
        )
        hoje = timezone.localdate()
        self.lancamento_cashback = LancamentoCashback.objects.create(
            matriz=self.matriz,
            loja=self.loja,
            chave_idempotencia=uuid.uuid4(),
            cliente=self.cliente_pdv,
            valor_compra=Decimal("100.00"),
            valor_base_cashback=Decimal("100.00"),
            percentual_cashback=Decimal("10.00"),
            valor_cashback=Decimal("10.00"),
            valor_utilizado=Decimal("2.00"),
            data_compra=hoje,
            data_liberacao=hoje,
            data_expiracao=hoje + timedelta(days=30),
        )
        self.voucher = Voucher.objects.create(
            matriz=self.matriz,
            cliente=self.cliente_pdv,
            codigo="PDV10",
            nome="Voucher PDV",
            tipo=Voucher.Tipo.PERCENTUAL,
            percentual=Decimal("10.00"),
            data_inicio=hoje,
            data_fim=hoje + timedelta(days=30),
            limite_utilizacao=1,
        )
        self.client.force_login(self.usuario)

    def test_inicio_exibe_caixa_aberto(self):
        resposta = self.client.get(reverse("pdv:inicio"))
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, "Caixa aberto")
        self.assertContains(resposta, "Produto")

    def test_busca_produto_ativo(self):
        resposta = self.client.get(
            reverse("pdv:buscar_produtos"),
            {"q": "Frente"},
        )
        self.assertEqual(resposta.status_code, 200)
        self.assertTrue(resposta.json()["ok"])
        self.assertEqual(resposta.json()["produtos"][0]["id"], self.produto.id)

    def test_adicionar_alterar_e_cancelar_item(self):
        resposta = self.client.post(
            reverse("pdv:adicionar_item"),
            {"produto_id": self.produto.id, "quantidade": "2.000"},
        )
        self.assertEqual(resposta.status_code, 200)
        venda = resposta.json()["venda"]
        self.assertEqual(venda["total"], "40.00")
        item_id = venda["itens"][0]["id"]

        resposta = self.client.post(
            reverse("pdv:alterar_item", args=[item_id]),
            {"quantidade": "3.000", "desconto": "5.00"},
        )
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.json()["venda"]["total"], "55.00")

        resposta = self.client.post(
            reverse("pdv:cancelar_item", args=[item_id]),
            {"motivo": "Teste de cancelamento"},
        )
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.json()["venda"]["total"], "0.00")
        self.assertEqual(resposta.json()["venda"]["itens"], [])

    def test_buscar_e_selecionar_cliente(self):
        resposta = self.client.get(reverse("pdv:buscar_clientes"), {"q": "Frente Caixa"})
        self.assertEqual(resposta.status_code, 200)
        self.assertTrue(resposta.json()["ok"])
        self.assertEqual(resposta.json()["clientes"][0]["id"], self.cliente_pdv.id)

        resposta = self.client.post(
            reverse("pdv:selecionar_cliente"),
            {"cliente_id": self.cliente_pdv.id},
        )
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.json()["venda"]["cliente"]["id"], self.cliente_pdv.id)

    def test_buscar_e_selecionar_vendedor(self):
        resposta = self.client.get(reverse("pdv:buscar_vendedores"))
        self.assertEqual(resposta.status_code, 200)
        self.assertIn(
            self.vendedor.id,
            [item["id"] for item in resposta.json()["vendedores"]],
        )

        resposta = self.client.post(
            reverse("pdv:selecionar_vendedor"),
            {"vendedor_id": self.vendedor.id},
        )
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.json()["venda"]["vendedor"]["id"], self.vendedor.id)

    def test_cliente_e_vendedor_persistem_na_venda(self):
        self.client.post(reverse("pdv:selecionar_cliente"), {"cliente_id": self.cliente_pdv.id})
        self.client.post(reverse("pdv:selecionar_vendedor"), {"vendedor_id": self.vendedor.id})

        resposta = self.client.get(reverse("pdv:estado_venda"))
        venda = resposta.json()["venda"]
        self.assertEqual(venda["cliente"]["id"], self.cliente_pdv.id)
        self.assertEqual(venda["vendedor"]["id"], self.vendedor.id)

    def test_beneficios_do_cliente_sao_exibidos_no_estado(self):
        self.client.post(
            reverse("pdv:selecionar_cliente"),
            {"cliente_id": self.cliente_pdv.id},
        )

        resposta = self.client.get(reverse("pdv:estado_venda"))
        beneficios = resposta.json()["venda"]["beneficios"]

        self.assertEqual(beneficios["cashback_disponivel"], "8")
        self.assertEqual(beneficios["cashback_previsto"], "0.00")
        self.assertIsNone(beneficios["voucher_recomendado"])

    def test_voucher_recomendado_e_desconto_atualizam_com_total(self):
        self.client.post(
            reverse("pdv:selecionar_cliente"),
            {"cliente_id": self.cliente_pdv.id},
        )
        resposta = self.client.post(
            reverse("pdv:adicionar_item"),
            {"produto_id": self.produto.id, "quantidade": "2.000"},
        )

        beneficios = resposta.json()["venda"]["beneficios"]
        self.assertEqual(beneficios["voucher_recomendado"]["id"], self.voucher.id)
        self.assertEqual(beneficios["desconto_recomendado"], "4.00")

    def test_cashback_previsto_reutiliza_configuracao_da_matriz(self):
        self.client.post(
            reverse("pdv:selecionar_cliente"),
            {"cliente_id": self.cliente_pdv.id},
        )
        resposta = self.client.post(
            reverse("pdv:adicionar_item"),
            {"produto_id": self.produto.id, "quantidade": "3.000"},
        )

        beneficios = resposta.json()["venda"]["beneficios"]
        self.assertEqual(beneficios["percentual_cashback"], "5.00")
        self.assertEqual(beneficios["cashback_previsto"], "3.00")

    @patch("pdv.views.fechar_venda_web")
    def test_endpoint_finaliza_com_payload_seguro(self, fechar_mock):
        resposta_item = self.client.post(
            reverse("pdv:adicionar_item"),
            {"produto_id": self.produto.id, "quantidade": "1.000"},
        )
        venda_id = resposta_item.json()["venda"]["id"]
        venda = Venda.objects.get(pk=venda_id)

        def fechar_simulado(**kwargs):
            venda_recebida = kwargs["venda"]
            venda_recebida.status = StatusOperacaoVenda.FINALIZADA
            venda_recebida.finalizada_em = timezone.now()
            venda_recebida.save(
                update_fields=["status", "finalizada_em", "atualizada_em"]
            )
            return venda_recebida

        fechar_mock.side_effect = fechar_simulado
        payload = {
            "tipo_beneficio": "nenhum",
            "valor_cashback": "0.00",
            "codigo_voucher": "",
            "pagamentos": [
                {
                    "forma_pagamento_id": 1,
                    "valor": "20.00",
                    "parcelas": 1,
                    "valor_recebido": "",
                }
            ],
        }

        resposta = self.client.post(
            reverse("pdv:finalizar_venda"),
            data=json.dumps(payload),
            content_type="application/json",
        )

        self.assertEqual(resposta.status_code, 200)
        self.assertTrue(resposta.json()["ok"])
        self.assertEqual(
            resposta.json()["venda"]["status"],
            StatusOperacaoVenda.FINALIZADA,
        )
        fechar_mock.assert_called_once()
        chamada = fechar_mock.call_args.kwargs
        self.assertEqual(chamada["venda"].pk, venda_id)
        self.assertEqual(chamada["usuario"], self.usuario)
        self.assertEqual(chamada["tipo_beneficio"], "nenhum")
        self.assertEqual(chamada["pagamentos"], payload["pagamentos"])
        self.assertIsNotNone(chamada["request"])

    @patch("pdv.views.fechar_venda_web")
    def test_endpoint_rejeita_fechamento_sem_pagamentos(self, fechar_mock):
        self.client.post(
            reverse("pdv:adicionar_item"),
            {"produto_id": self.produto.id, "quantidade": "1.000"},
        )
        fechar_mock.side_effect = ValidationError({
            "pagamentos": "A venda deve possuir pelo menos um pagamento."
        })

        resposta = self.client.post(
            reverse("pdv:finalizar_venda"),
            data=json.dumps({
                "tipo_beneficio": "nenhum",
                "pagamentos": [],
            }),
            content_type="application/json",
        )

        self.assertEqual(resposta.status_code, 400)
        self.assertFalse(resposta.json()["ok"])
        self.assertIn("pagamento", resposta.json()["erro"].lower())
        fechar_mock.assert_called_once()

    def test_endpoint_rejeita_json_invalido(self):
        self.client.post(
            reverse("pdv:adicionar_item"),
            {"produto_id": self.produto.id, "quantidade": "1.000"},
        )

        resposta = self.client.post(
            reverse("pdv:finalizar_venda"),
            data="{json-invalido",
            content_type="application/json",
        )

        self.assertEqual(resposta.status_code, 400)
        self.assertFalse(resposta.json()["ok"])
        self.assertIn("inválidos", resposta.json()["erro"].lower())

    def test_endpoint_finalizacao_exige_venda_atual(self):
        resposta = self.client.post(reverse("pdv:finalizar_venda"))

        self.assertEqual(resposta.status_code, 404)
        self.assertFalse(resposta.json()["ok"])


# PDV-04.2 V5 - TESTES VOUCHER/CANCELAMENTO
