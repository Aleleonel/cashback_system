from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from empresas.models import Loja, Matriz
from configuracoes.models import ConfiguracaoComissaoMatriz, FechamentoComissao, MetaComissaoLoja

class ComissoesUIFechamentoPostFuncionalTests(TestCase):
    def setUp(self):
        self.m1 = Matriz.objects.create(nome="Matriz Fechamento A")
        self.m2 = Matriz.objects.create(nome="Matriz Fechamento B")
        self.l1 = Loja.objects.create(nome="Loja Fechamento A", matriz=self.m1)
        self.l2 = Loja.objects.create(nome="Loja Fechamento B", matriz=self.m2)
        self.user = get_user_model().objects.create_user(
            username="f2d58_post", password="x", perfil="admin_loja",
            matriz=self.m1, ativo=True
        )
        self.client.force_login(self.user)
        ConfiguracaoComissaoMatriz.objects.create(
            matriz=self.m1, exigir_minimo_individual=False,
            minimo_vendas_vendedor=Decimal("0.00")
        )
        MetaComissaoLoja.objects.create(
            loja=self.l1, valor_meta=Decimal("50000.00"),
            percentual_comissao=Decimal("1.5000"), ativa=True
        )
        self.url = reverse("configuracoes:comissoes")

    def post_fechamento(self, loja, ano="2026", mes="9"):
        return self.client.post(self.url, {
            "acao": "fechamento_comissao",
            "loja_fechamento_id": str(loja.pk),
            "competencia_ano": ano,
            "competencia_mes": mes,
        })

    def test_fecha_competencia_da_loja_do_proprio_escopo(self):
        resposta = self.post_fechamento(self.l1)
        self.assertEqual(resposta.status_code, 302)
        self.assertTrue(FechamentoComissao.objects.filter(
            matriz=self.m1, loja=self.l1,
            competencia_ano=2026, competencia_mes=9
        ).exists())

    def test_rejeita_fechamento_de_loja_de_outra_matriz(self):
        resposta = self.post_fechamento(self.l2)
        self.assertEqual(resposta.status_code, 200)
        self.assertFalse(FechamentoComissao.objects.filter(loja=self.l2).exists())

    def test_rejeita_mes_e_ano_invalidos_sem_criar_fechamento(self):
        for ano, mes in (("2026", "0"), ("2026", "13"), ("0", "9"), ("abc", "9"), ("2026", "abc")):
            with self.subTest(ano=ano, mes=mes):
                resposta = self.post_fechamento(self.l1, ano=ano, mes=mes)
                self.assertEqual(resposta.status_code, 200)
        self.assertFalse(FechamentoComissao.objects.filter(loja=self.l1).exists())

    def test_repeticao_post_preserva_um_unico_snapshot(self):
        primeira = self.post_fechamento(self.l1)
        self.assertEqual(primeira.status_code, 302)
        fechamento = FechamentoComissao.objects.get(
            loja=self.l1, competencia_ano=2026, competencia_mes=9
        )
        percentual_original = fechamento.percentual_aplicado
        MetaComissaoLoja.objects.filter(loja=self.l1).update(
            percentual_comissao=Decimal("9.0000")
        )
        segunda = self.post_fechamento(self.l1)
        self.assertEqual(segunda.status_code, 302)
        self.assertEqual(FechamentoComissao.objects.filter(
            loja=self.l1, competencia_ano=2026, competencia_mes=9
        ).count(), 1)
        fechamento.refresh_from_db()
        self.assertEqual(fechamento.percentual_aplicado, percentual_original)

    def test_historico_nao_expoe_fechamento_de_outra_matriz(self):
        FechamentoComissao.objects.create(
            matriz=self.m2, loja=self.l2, competencia_ano=2026, competencia_mes=8,
            total_vendas_loja=Decimal("0.00"), valor_meta_atingida=None,
            percentual_aplicado=Decimal("0.0000"),
            exigir_minimo_individual=False, minimo_individual=Decimal("0.00")
        )
        resposta = self.client.get(self.url)
        self.assertEqual(resposta.status_code, 200)
        self.assertNotContains(resposta, "Loja Fechamento B")
        self.assertFalse(any(f.loja_id == self.l2.pk for f in resposta.context["fechamentos_comissao"]))