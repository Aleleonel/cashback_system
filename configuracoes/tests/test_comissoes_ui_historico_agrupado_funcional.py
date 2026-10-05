from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from empresas.models import Loja, Matriz
from configuracoes.models import ComissaoVendedor, FechamentoComissao

class ComissoesUIHistoricoAgrupadoFuncionalTests(TestCase):
    def setUp(self):
        self.matriz = Matriz.objects.create(nome="Matriz Historico")
        self.loja = Loja.objects.create(nome="Loja Historico", matriz=self.matriz)
        User = get_user_model()
        self.admin = User.objects.create_user(
            username="f2d58_hist_admin", password="x", perfil="admin_loja",
            matriz=self.matriz, ativo=True
        )
        self.vendedor = User.objects.create_user(
            username="f2d58_hist_vend", password="x", first_name="Vendedor",
            last_name="Historico", matriz=self.matriz, ativo=True
        )
        self.client.force_login(self.admin)
        self.com_detalhe = FechamentoComissao.objects.create(
            matriz=self.matriz, loja=self.loja, competencia_ano=2026, competencia_mes=9,
            total_vendas_loja=Decimal("50000.00"), valor_meta_atingida=Decimal("50000.00"),
            percentual_aplicado=Decimal("1.5000"), exigir_minimo_individual=False,
            minimo_individual=Decimal("0.00")
        )
        self.sem_detalhe = FechamentoComissao.objects.create(
            matriz=self.matriz, loja=self.loja, competencia_ano=2026, competencia_mes=8,
            total_vendas_loja=Decimal("1000.00"), valor_meta_atingida=None,
            percentual_aplicado=Decimal("0.0000"), exigir_minimo_individual=False,
            minimo_individual=Decimal("0.00")
        )
        ComissaoVendedor.objects.create(
            fechamento=self.com_detalhe, vendedor=self.vendedor,
            vendedor_uuid_original=self.vendedor.uuid,
            vendedor_nome_original="Vendedor Historico",
            total_vendas_vendedor=Decimal("50000.00"), elegivel=True,
            valor_comissao=Decimal("750.00")
        )

    def test_view_entrega_detalhes_agrupados_no_proprio_fechamento(self):
        resposta = self.client.get(reverse("configuracoes:comissoes"))
        self.assertEqual(resposta.status_code, 200)
        fechamentos = list(resposta.context["fechamentos_comissao"])
        f9 = next(f for f in fechamentos if f.pk == self.com_detalhe.pk)
        f8 = next(f for f in fechamentos if f.pk == self.sem_detalhe.pk)
        self.assertEqual([c.vendedor_nome_original for c in f9.comissoes_vendedores.all()], ["Vendedor Historico"])
        self.assertEqual(list(f8.comissoes_vendedores.all()), [])

    def test_template_usa_relacao_do_fechamento_e_estado_vazio_por_fechamento(self):
        resposta = self.client.get(reverse("configuracoes:comissoes"))
        self.assertEqual(resposta.status_code, 200)
        html = resposta.content.decode("utf-8")
        self.assertIn("Vendedor Historico", html)
        self.assertIn("Nenhuma comissão individual registrada.", html)
        self.assertEqual(html.count("Vendedor Historico"), 1)

    def test_template_nao_depende_de_lista_global_de_comissoes(self):
        resposta = self.client.get(reverse("configuracoes:comissoes"))
        self.assertEqual(resposta.status_code, 200)
        self.assertNotIn("comissoes_vendedores", resposta.context)