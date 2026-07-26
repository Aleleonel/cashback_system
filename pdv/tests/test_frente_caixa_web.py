from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from empresas.models import Loja, Matriz
from pdv.models import Caixa, SessaoCaixa
from produtos.choices import StatusProduto
from produtos.models import Produto, UnidadeMedida


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
