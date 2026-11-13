from datetime import date
from decimal import Decimal
from urllib.parse import parse_qs, urlsplit
import csv
import io

from django.test import TestCase
from django.urls import reverse
from accounts.models import Usuario
from empresas.models import Loja, Matriz
from financeiro.models import TituloFinanceiro
from financeiro.services import criar_titulo_financeiro


class AP7RPeriodoHTTPTests(TestCase):
    def setUp(self):
        self.matriz = Matriz.objects.create(nome="AP7R Matriz")
        self.outra = Matriz.objects.create(nome="AP7R Outra")
        self.loja = Loja.objects.create(matriz=self.matriz, nome="AP7R Loja")
        self.loja2 = Loja.objects.create(matriz=self.matriz, nome="AP7R Loja 2")
        self.loja_outra = Loja.objects.create(matriz=self.outra, nome="AP7R Loja Outra")
        self.master = Usuario.objects.create_user(username="ap7r_master", password="teste123", matriz=self.matriz, perfil=Usuario.PERFIL_MASTER)
        self.operador = Usuario.objects.create_user(username="ap7r_operador", password="teste123", matriz=self.matriz, perfil=Usuario.PERFIL_OPERADOR)
        self.operador.lojas.add(self.loja)
        self.t1 = self.criar("AP7R-ALVO", self.matriz, self.loja, date(2026, 11, 12), date(2026, 11, 12), [date(2026, 11, 12), date(2026, 11, 13)])
        self.t2 = self.criar("AP7R-FORA", self.matriz, self.loja, date(2026, 11, 13), date(2026, 11, 13), [date(2026, 11, 14)])
        self.t3 = self.criar("AP7R-OUTRA-LOJA", self.matriz, self.loja2, date(2026, 11, 12), date(2026, 11, 12), [date(2026, 11, 12)])
        self.t4 = self.criar("AP7R-OUTRA-MATRIZ", self.outra, self.loja_outra, date(2026, 11, 12), date(2026, 11, 12), [date(2026, 11, 12)])
        self.client.force_login(self.master)

    def criar(self, descricao, matriz, loja, emissao, competencia, vencimentos):
        titulo = criar_titulo_financeiro(
            matriz=matriz, loja=loja, natureza=TituloFinanceiro.Natureza.PAGAR,
            origem_tipo=TituloFinanceiro.OrigemTipo.MANUAL, origem_id=descricao,
            chave_idempotencia=descricao, descricao=descricao, data_emissao=emissao,
            parcelas=[{"numero": i + 1, "vencimento": vencimento, "valor": Decimal("10.00")} for i, vencimento in enumerate(vencimentos)],
            usuario=None,
        )
        TituloFinanceiro.objects.filter(pk=titulo.pk).update(data_competencia=competencia)
        return titulo

    def params(self, **kwargs):
        d = {"escopo": "loja", "loja": str(self.loja.pk)}
        d.update(kwargs)
        return d

    def lista(self, **kwargs):
        return self.client.get(reverse("financeiro:titulos"), self.params(**kwargs))

    def csv_response(self, **kwargs):
        return self.client.get(reverse("financeiro:titulos_exportar_csv"), self.params(**kwargs))

    def test_emissao_inclusiva(self):
        r = self.lista(criterio_data="emissao", data_inicio="2026-11-12", data_fim="2026-11-12")
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "AP7R-ALVO")
        self.assertNotContains(r, "AP7R-FORA")
        self.assertNotContains(r, "AP7R-OUTRA-LOJA")
        self.assertNotContains(r, "AP7R-OUTRA-MATRIZ")

    def test_competencia_inclusiva(self):
        r = self.lista(criterio_data="competencia", data_inicio="2026-11-12", data_fim="2026-11-12")
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "AP7R-ALVO")
        self.assertNotContains(r, "AP7R-FORA")

    def test_vencimento_sem_duplicar_titulo(self):
        r = self.lista(criterio_data="vencimento", data_inicio="2026-11-12", data_fim="2026-11-13")
        self.assertEqual(r.status_code, 200)
        ids = [x.pk for x in r.context["pagina"].object_list]
        self.assertEqual(ids.count(self.t1.pk), 1)
        self.assertNotIn(self.t2.pk, ids)

    def test_periodo_sem_datas_nao_restringe(self):
        r = self.lista(criterio_data="emissao")
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "AP7R-ALVO")
        self.assertContains(r, "AP7R-FORA")

    def test_data_invertida_lista_e_csv(self):
        d = {"criterio_data": "emissao", "data_inicio": "2026-11-13", "data_fim": "2026-11-12"}
        r = self.lista(**d)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context["pagina"].paginator.count, 0)
        self.assertTrue(r.context["erros_periodo"])
        self.assertEqual(self.csv_response(**d).status_code, 400)

    def test_data_invalida_lista_e_csv(self):
        d = {"criterio_data": "competencia", "data_inicio": "2026-99-99"}
        r = self.lista(**d)
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.context["erros_periodo"])
        self.assertEqual(self.csv_response(**d).status_code, 400)

    def test_csv_mesmos_titulos_do_filtro(self):
        d = {"criterio_data": "vencimento", "data_inicio": "2026-11-12", "data_fim": "2026-11-13"}
        lista = self.lista(**d)
        export = self.csv_response(**d)
        self.assertEqual(export.status_code, 200)
        self.assertIn("text/csv", export["Content-Type"])
        rows = list(csv.reader(io.StringIO(export.content.decode("utf-8-sig")), delimiter=";"))
        descricoes = [row[2] for row in rows[1:]]
        self.assertEqual(descricoes.count("AP7R-ALVO"), 1)
        self.assertNotIn("AP7R-FORA", descricoes)
        self.assertEqual(len(descricoes), lista.context["pagina"].paginator.count)

    def test_detalhes_preservam_query_e_voltar(self):
        d = self.params(criterio_data="competencia", data_inicio="2026-11-12", data_fim="2026-11-12")
        lista = self.client.get(reverse("financeiro:titulos"), d)
        self.assertEqual(lista.status_code, 200)
        html = lista.content.decode()
        self.assertIn("criterio_data=competencia", html)
        detalhe = self.client.get(reverse("financeiro:titulo_detalhe", args=[self.t1.uuid]), d)
        self.assertEqual(detalhe.status_code, 200)
        self.assertIn("data_inicio=2026-11-12", detalhe.content.decode())
        self.assertIn("data_fim=2026-11-12", detalhe.content.decode())

    def test_limpar_filtros_aponta_para_rota_sem_query(self):
        r = self.lista(criterio_data="competencia", data_inicio="2026-11-12")
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'href="' + reverse("financeiro:titulos") + '" class="btn btn-outline-secondary me-2">Limpar filtros')

    def test_matriz_outra_nao_vaza_lista_csv(self):
        r = self.client.get(reverse("financeiro:titulos"), {"escopo": "consolidado"})
        self.assertEqual(r.status_code, 200)
        self.assertNotContains(r, "AP7R-OUTRA-MATRIZ")
        e = self.client.get(reverse("financeiro:titulos_exportar_csv"), {"escopo": "consolidado"})
        self.assertEqual(e.status_code, 200)
        self.assertNotIn("AP7R-OUTRA-MATRIZ", e.content.decode())

    def test_loja_de_outra_matriz_negada(self):
        for rota in ("financeiro:titulos", "financeiro:titulos_exportar_csv"):
            r = self.client.get(reverse(rota), {"escopo": "loja", "loja": self.loja_outra.pk})
            self.assertEqual(r.status_code, 404)

    def test_operador_sem_permissao_bloqueado(self):
        self.client.force_login(self.operador)
        for rota in ("financeiro:titulos", "financeiro:titulos_exportar_csv"):
            r = self.client.get(reverse(rota), self.params())
            self.assertIn(r.status_code, (302, 403))

    def test_sem_login_nao_acessa(self):
        self.client.logout()
        for rota in ("financeiro:titulos", "financeiro:titulos_exportar_csv"):
            self.assertEqual(self.client.get(reverse(rota)).status_code, 302)
