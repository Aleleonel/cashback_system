from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from configuracoes.models import FechamentoComissao
from empresas.models import Loja, Matriz


class F31QHistoricoCompetenciaTests(TestCase):
    def setUp(self):
        self.matriz = Matriz.objects.create(nome="Matriz F31Q")
        self.loja = Loja.objects.create(nome="Loja F31Q", matriz=self.matriz)
        User = get_user_model()
        self.user = User.objects.create_user(
            username="f31q_admin",
            password="teste-f31q",
            is_superuser=True,
            is_staff=True,
        )
        self.client.force_login(self.user)

        hoje = timezone.localdate()
        self.ano_atual = hoje.year
        self.mes_atual = hoje.month
        if hoje.month == 1:
            self.ano_anterior, self.mes_anterior = hoje.year - 1, 12
        else:
            self.ano_anterior, self.mes_anterior = hoje.year, hoje.month - 1

        self.atual = FechamentoComissao.objects.create(
            matriz=self.matriz, loja=self.loja,
            competencia_ano=self.ano_atual, competencia_mes=self.mes_atual,
            total_vendas_loja="100.00", percentual_aplicado="5.00",
            exigir_minimo_individual=False,
        )
        self.anterior = FechamentoComissao.objects.create(
            matriz=self.matriz, loja=self.loja,
            competencia_ano=self.ano_anterior, competencia_mes=self.mes_anterior,
            total_vendas_loja="80.00", percentual_aplicado="4.00",
            exigir_minimo_individual=False,
        )

    def _url(self, **params):
        base = reverse("configuracoes:comissoes")
        query = {"matriz": self.matriz.pk}
        query.update(params)
        return base + "?" + "&".join(f"{k}={v}" for k, v in query.items())

    def test_sem_filtro_exibe_somente_competencia_vigente(self):
        resposta = self.client.get(self._url())
        self.assertEqual(resposta.status_code, 200)
        ids = [f.pk for f in resposta.context["fechamentos_comissao"]]
        self.assertIn(self.atual.pk, ids)
        self.assertNotIn(self.anterior.pk, ids)
        self.assertEqual(resposta.context["historico_ano"], self.ano_atual)
        self.assertEqual(resposta.context["historico_mes"], self.mes_atual)

    def test_filtro_mes_ano_exibe_competencia_solicitada(self):
        resposta = self.client.get(self._url(
            historico_ano=self.ano_anterior,
            historico_mes=self.mes_anterior,
        ))
        self.assertEqual(resposta.status_code, 200)
        ids = [f.pk for f in resposta.context["fechamentos_comissao"]]
        self.assertIn(self.anterior.pk, ids)
        self.assertNotIn(self.atual.pk, ids)

    def test_filtro_invalido_retorna_para_competencia_vigente(self):
        resposta = self.client.get(self._url(historico_ano="abc", historico_mes="99"))
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.context["historico_ano"], self.ano_atual)
        self.assertEqual(resposta.context["historico_mes"], self.mes_atual)

    def test_template_tem_filtro_e_colunas_detalhes_estaveis(self):
        template = (
            Path(settings.BASE_DIR) / "configuracoes" / "templates"
            / "configuracoes" / "comissoes.html"
        ).read_text(encoding="utf-8")
        self.assertIn('name="historico_mes"', template)
        self.assertIn('name="historico_ano"', template)
        self.assertIn("Competência exibida:", template)
        self.assertIn("min-width: 8.5rem;", template)
        self.assertIn("text-end text-nowrap", template)
