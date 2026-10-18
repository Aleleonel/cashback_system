from datetime import date
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from configuracoes.models import ComissaoVendedor, FechamentoComissao
from empresas.models import Matriz, Loja
from financeiro.models import TituloFinanceiro


class F24HttpDinamicoTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="f24-http-master", password="senha-f24", perfil="master"
        )
        self.matriz = Matriz.objects.create(nome="Matriz F24 HTTP")
        self.loja = Loja.objects.create(nome="Loja F24 HTTP", matriz=self.matriz)
        self.user.matriz = self.matriz
        self.user.save(update_fields=["matriz"])
        self.fechamento = FechamentoComissao.objects.create(
            matriz=self.matriz, loja=self.loja,
            competencia_ano=2026, competencia_mes=10,
            total_vendas_loja=Decimal("1000.00"),
            percentual_aplicado=Decimal("5.0000"),
            exigir_minimo_individual=False,
            minimo_individual=Decimal("0.00"),
        )
        self.comissao = ComissaoVendedor.objects.create(
            fechamento=self.fechamento, vendedor=self.user,
            vendedor_uuid_original=self.user.pk,
            vendedor_nome_original="Vendedor F24",
            total_vendas_vendedor=Decimal("1000.00"),
            elegivel=True, valor_comissao=Decimal("50.00"),
        )
        self.client.force_login(self.user)
        self.url = reverse("configuracoes:comissoes")

    def post(self, **extra):
        data={"acao":"provisionar_comissao","comissao_id":str(self.comissao.pk),"vencimento":"2026-10-31"}
        data.update(extra)
        return self.client.post(self.url, data)

    @patch("configuracoes.views.usuario_tem_permissao", return_value=False)
    def test_sem_permissao_nao_cria_titulo(self, _):
        self.post()
        self.assertFalse(TituloFinanceiro.objects.filter(origem_tipo="COMISSAO").exists())

    @patch("configuracoes.views.usuario_tem_permissao", return_value=True)
    def test_vencimento_ausente_ou_invalido_nao_cria_titulo(self, _):
        self.post(vencimento="")
        self.post(vencimento="31/10/2026")
        self.assertFalse(TituloFinanceiro.objects.filter(origem_tipo="COMISSAO").exists())

    @patch("configuracoes.views.usuario_tem_permissao", return_value=True)
    def test_comissao_fora_da_matriz_nao_cria_titulo(self, _):
        outra=Matriz.objects.create(nome="Outra Matriz F24")
        outra_loja=Loja.objects.create(nome="Outra Loja F24", matriz=outra)
        f=FechamentoComissao.objects.create(
            matriz=outra, loja=outra_loja, competencia_ano=2026, competencia_mes=10,
            total_vendas_loja=Decimal("500.00"), percentual_aplicado=Decimal("5.0000"),
            exigir_minimo_individual=False, minimo_individual=Decimal("0.00"),
        )
        c=ComissaoVendedor.objects.create(
            fechamento=f, vendedor=self.user, vendedor_uuid_original=self.user.pk,
            vendedor_nome_original="Fora Escopo", total_vendas_vendedor=Decimal("500.00"),
            elegivel=True, valor_comissao=Decimal("25.00"),
        )
        self.post(comissao_id=str(c.pk))
        self.assertFalse(TituloFinanceiro.objects.filter(origem_tipo="COMISSAO",origem_id=str(c.pk)).exists())

    @patch("configuracoes.views.usuario_tem_permissao", return_value=True)
    def test_post_valido_cria_um_titulo_parcela_e_preserva_snapshot(self, _):
        antes=(self.comissao.elegivel,self.comissao.valor_comissao,self.comissao.total_vendas_vendedor)
        self.post()
        qs=TituloFinanceiro.objects.filter(origem_tipo="COMISSAO",origem_id=str(self.comissao.pk))
        self.assertEqual(qs.count(),1)
        titulo=qs.get()
        self.assertEqual(titulo.natureza,"PAGAR")
        self.assertEqual(titulo.loja_id,self.loja.pk)
        self.assertEqual(titulo.parcelas.count(),1)
        parcela=titulo.parcelas.get()
        self.assertEqual(parcela.vencimento,date(2026,10,31))
        self.assertEqual(parcela.valor_original,Decimal("50.00"))
        self.comissao.refresh_from_db()
        depois=(self.comissao.elegivel,self.comissao.valor_comissao,self.comissao.total_vendas_vendedor)
        self.assertEqual(antes,depois)

    @patch("configuracoes.views.usuario_tem_permissao", return_value=True)
    def test_repeticao_mesmo_vencimento_e_idempotente(self, _):
        self.post(); self.post()
        self.assertEqual(TituloFinanceiro.objects.filter(origem_tipo="COMISSAO",origem_id=str(self.comissao.pk)).count(),1)

    @patch("configuracoes.views.usuario_tem_permissao", return_value=True)
    def test_comissao_zero_nao_cria_titulo(self, _):
        ComissaoVendedor.objects.filter(pk=self.comissao.pk).update(valor_comissao=Decimal("0.00"))
        self.post()
        self.assertFalse(TituloFinanceiro.objects.filter(origem_tipo="COMISSAO", origem_id=str(self.comissao.pk)).exists())

    @patch("configuracoes.views.usuario_tem_permissao", return_value=True)
    def test_comissao_inelegivel_nao_cria_titulo(self, _):
        ComissaoVendedor.objects.filter(pk=self.comissao.pk).update(elegivel=False)
        self.post()
        self.assertFalse(TituloFinanceiro.objects.filter(origem_tipo="COMISSAO", origem_id=str(self.comissao.pk)).exists())

    @patch("configuracoes.views.usuario_tem_permissao", return_value=True)
    def test_get_real_titulo_detalhe_com_escopo_loja(self, _):
        self.post()
        titulo=TituloFinanceiro.objects.get(origem_tipo="COMISSAO", origem_id=str(self.comissao.pk))
        url=reverse("financeiro:titulo_detalhe", args=[titulo.uuid])+"?escopo=loja&loja="+str(self.loja.pk)
        response=self.client.get(url)
        self.assertEqual(response.status_code, 200)

    @patch("configuracoes.views.usuario_tem_permissao", return_value=True)
    def test_titulo_existente_aparece_com_link_escopo_loja(self, _):
        self.post()
        response=self.client.get(self.url)
        self.assertEqual(response.status_code,200)
        titulo=TituloFinanceiro.objects.get(origem_tipo="COMISSAO",origem_id=str(self.comissao.pk))
        alvo=reverse("financeiro:titulo_detalhe",args=[titulo.uuid])
        self.assertContains(response, alvo+"?escopo=loja&loja="+str(self.loja.pk), html=False)