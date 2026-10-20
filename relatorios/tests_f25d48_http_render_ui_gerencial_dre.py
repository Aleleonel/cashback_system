from datetime import date
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from empresas.models import Matriz, Loja, StatusOperacional
from relatorios.services_dre import ResultadoDRE, ComparativoDRE


def resultado(base=Decimal("100.00")):
    return ResultadoDRE(
        receita_bruta=base,
        acrescimos=Decimal("0"),
        deducoes_receita=Decimal("10"),
        receita_liquida=base-Decimal("10"),
        cmv=Decimal("30"),
        lucro_bruto=base-Decimal("40"),
        despesas_operacionais=Decimal("20"),
        resultado_operacional=base-Decimal("60"),
        resultado_financeiro=Decimal("5"),
        outras_receitas_despesas=Decimal("-2"),
        resultado_antes_impostos=base-Decimal("57"),
        margem_bruta=Decimal("66.67"),
        margem_operacional=Decimal("44.44"),
        memoria_calculo={},
    )


class DREHTTPRenderGerencialTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.matriz=Matriz.objects.create(nome="F25D48 Matriz",cnpj="66.666.666/0001-66")
        cls.loja=Loja.objects.create(matriz=cls.matriz,nome="F25D48 Loja",cnpj="66.666.666/0002-47",status=StatusOperacional.ATIVA)
        U=get_user_model()
        cls.user=U.objects.create_user(username="f25d48_admin",password="x",matriz=cls.matriz,perfil="admin_loja")
        cls.user.lojas.add(cls.loja)

    def setUp(self):
        self.client.force_login(self.user)

    def ctx(self):
        atual=resultado()
        anterior=resultado(Decimal("80.00"))
        campos=("receita_bruta","deducoes_receita","receita_liquida","cmv","lucro_bruto","despesas_operacionais","resultado_operacional","resultado_financeiro","outras_receitas_despesas","resultado_antes_impostos")
        va={c:getattr(atual,c)-getattr(anterior,c) for c in campos}
        vp={c:Decimal("25.00") for c in campos}
        comp=ComparativoDRE(atual=atual,anterior=anterior,variacao_absoluta=va,variacao_percentual=vp)
        drill={
          "receita_bruta":{"vendas":[101]},
          "deducoes_receita":{"vendas":[101],"titulos":[201]},
          "cmv":{"itens_venda":[301]},
          "despesas_operacionais":{"titulos":[202],"comissoes":[401]},
          "resultado_financeiro":{"titulos":[203]},
          "outras_receitas_despesas":{"titulos":[204]},
          "receita_liquida":{"tipo":"DERIVADO","formula":"receita_bruta - deducoes_receita","componentes":["receita_bruta","deducoes_receita"]},
          "lucro_bruto":{"tipo":"DERIVADO","formula":"receita_liquida - cmv","componentes":["receita_liquida","cmv"]},
          "resultado_operacional":{"tipo":"DERIVADO","formula":"lucro_bruto - despesas_operacionais","componentes":["lucro_bruto","despesas_operacionais"]},
          "resultado_antes_impostos":{"tipo":"DERIVADO","formula":"resultado_operacional + resultado_financeiro + outras_receitas_despesas","componentes":["resultado_operacional","resultado_financeiro","outras_receitas_despesas"]},
        }
        return {
          "matriz":self.matriz,"matrizes":Matriz.objects.none(),"matriz_selecionada":str(self.matriz.pk),
          "lojas":[self.loja],"centros_custo":[],"loja_selecionada":"","centro_custo_selecionado":"",
          "data_inicio":date(2026,10,1),"data_fim":date(2026,10,31),
          "data_inicio_input":"2026-10-01","data_fim_input":"2026-10-31",
          "filtros_validos":True,"erro_filtros":[],
          "resultado":atual,"analise_vertical":{},"comparativo":comp,"drilldown":drill,
          "evolucao":[{"inicio":date(2026,10,1),"fim":date(2026,10,31),"resultado":atual}],
          "periodo_anterior":(date(2026,9,1),date(2026,9,30)),
        }

    @patch("relatorios.views._contexto_dre")
    def test_renderiza_cards_margens(self,m):
        m.return_value=self.ctx()
        r=self.client.get(reverse("relatorios:dre"))
        self.assertEqual(r.status_code,200)
        self.assertContains(r,"Margem Bruta")
        self.assertContains(r,"66,67%")
        self.assertContains(r,"Margem Operacional")

    @patch("relatorios.views._contexto_dre")
    def test_renderiza_origens_diretas_reais(self,m):
        m.return_value=self.ctx()
        r=self.client.get(reverse("relatorios:dre"))
        for token in ("#101","#201","#301","#202","#401","#203","#204"):
            self.assertContains(r,token)

    @patch("relatorios.views._contexto_dre")
    def test_renderiza_derivados_formula_componentes(self,m):
        m.return_value=self.ctx()
        r=self.client.get(reverse("relatorios:dre"))
        self.assertContains(r,"receita_bruta - deducoes_receita")
        self.assertContains(r,"lucro_bruto - despesas_operacionais")
        self.assertContains(r,"Componentes:")

    @patch("relatorios.views._contexto_dre")
    def test_renderiza_comparativo_com_variacoes(self,m):
        m.return_value=self.ctx()
        r=self.client.get(reverse("relatorios:dre"))
        self.assertContains(r,"Comparativo com periodo anterior")
        self.assertContains(r,"Variacao R$")
        self.assertContains(r,"Variacao %")
        self.assertContains(r,"25,00")

    @patch("relatorios.views._contexto_dre")
    def test_renderiza_evolucao_mensal(self,m):
        m.return_value=self.ctx()
        r=self.client.get(reverse("relatorios:dre"))
        self.assertContains(r,"Evolucao mensal")
        self.assertContains(r,"01/10/2026")
        self.assertContains(r,"31/10/2026")

    @patch("relatorios.views._contexto_dre")
    def test_sem_resultado_nao_vaza_blocos_gerenciais(self,m):
        c=self.ctx();c.update({"resultado":None,"comparativo":None,"drilldown":{},"evolucao":[],"filtros_validos":False,"erro_filtros":["Data inválida"]})
        m.return_value=c
        r=self.client.get(reverse("relatorios:dre"))
        self.assertEqual(r.status_code,200)
        self.assertContains(r,"Data inválida")
        self.assertNotContains(r,"Rastreabilidade gerencial")
        self.assertNotContains(r,"Comparativo com periodo anterior")

    def test_hub_financeiro_renderiza_acesso_dre(self):
        r=self.client.get(reverse("relatorios:financeiro"))
        self.assertEqual(r.status_code,200)
        self.assertContains(r,"DRE Gerencial")
        self.assertContains(r,reverse("relatorios:dre"))
