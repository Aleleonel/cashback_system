from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from accounts.permissions import PERMISSAO_FINANCEIRO_CANCELAR_LANCAMENTO
from empresas.models import Matriz, Loja
from financeiro.models import PlanoConta, TituloFinanceiro
from financeiro.services import criar_lancamento_manual

User = get_user_model()


class F26Z35CancelamentoWebFuncionalTests(TestCase):
    def setUp(self):
        self.matriz = Matriz.objects.create(nome="Matriz F26Z35")
        self.loja = Loja.objects.create(matriz=self.matriz, nome="Loja F26Z35")
        self.plano = PlanoConta.objects.create(
            matriz=self.matriz,
            codigo="F26Z35",
            nome="Despesa F26Z35",
            tipo=PlanoConta.Tipo.ANALITICA,
            natureza=PlanoConta.Natureza.DESPESA,
            aceita_lancamento=True,
        )
        self.user = User.objects.create_user(
            username="f26z35_admin",
            password="senha-f26z35",
            matriz=self.matriz,
            perfil=getattr(User, "PERFIL_MASTER", "master"),
        )
        if hasattr(self.user, "permissoes"):
            try:
                self.user.permissoes.add(PERMISSAO_FINANCEIRO_CANCELAR_LANCAMENTO)
            except Exception:
                pass
        self.client.force_login(self.user)

    def _titulo(self, *, origem=None):
        origem = origem or TituloFinanceiro.OrigemTipo.MANUAL
        if origem == TituloFinanceiro.OrigemTipo.MANUAL:
            return criar_lancamento_manual(
                matriz=self.matriz,
                loja=self.loja,
                natureza=TituloFinanceiro.Natureza.PAGAR,
                chave_idempotencia=f"f26z35-{TituloFinanceiro.objects.count()+1}",
                descricao="Titulo F26Z35",
                data_emissao=date(2026, 10, 23),
                parcelas=[{"numero": 1, "vencimento": date(2026, 10, 30), "valor": Decimal("100.00")}],
                plano_conta=self.plano,
                data_competencia=date(2026, 10, 1),
                valor_bruto=Decimal("100.00"),
                valor_desconto=Decimal("0.00"),
                valor_juros=Decimal("0.00"),
                usuario=self.user,
            )
        return TituloFinanceiro.objects.create(
            matriz=self.matriz, loja=self.loja,
            natureza=TituloFinanceiro.Natureza.PAGAR,
            origem_tipo=origem, origem_id="f26z35-auto",
            descricao="Automatico F26Z35",
            data_emissao=date(2026,10,23), data_competencia=date(2026,10,1),
            valor_bruto=Decimal("100.00"), valor_original=Decimal("100.00"),
            status=TituloFinanceiro.Status.ABERTO,
        )

    def _url(self, titulo, nome="financeiro:titulo_cancelar"):
        return reverse(nome, kwargs={"titulo_uuid": titulo.uuid}) + f"?escopo=loja&loja={self.loja.pk}"

    def test_get_manual_autorizado_renderiza_form(self):
        titulo=self._titulo()
        r=self.client.get(self._url(titulo))
        self.assertEqual(r.status_code,200)
        self.assertContains(r,"Motivo do cancelamento")
        self.assertContains(r,"estorno")
        self.assertContains(r,"origem automática")

    def test_post_motivo_vazio_nao_cancela(self):
        titulo=self._titulo()
        r=self.client.post(self._url(titulo),{"motivo":"   "})
        self.assertEqual(r.status_code,200)
        titulo.refresh_from_db()
        self.assertNotEqual(titulo.status,TituloFinanceiro.Status.CANCELADO)
        self.assertContains(r,"Motivo do cancelamento")

    def test_origem_automatica_get_bloqueado(self):
        titulo=self._titulo(origem=TituloFinanceiro.OrigemTipo.COMPRA_RECEBIMENTO)
        r=self.client.get(self._url(titulo))
        self.assertEqual(r.status_code,404)

    def test_detalhe_manual_aberto_expoe_cancelar(self):
        titulo=self._titulo()
        url=reverse("financeiro:titulo_detalhe",kwargs={"titulo_uuid":titulo.uuid})+f"?escopo=loja&loja={self.loja.pk}"
        r=self.client.get(url)
        self.assertEqual(r.status_code,200)
        self.assertContains(r,reverse("financeiro:titulo_cancelar",kwargs={"titulo_uuid":titulo.uuid}))

    def test_detalhe_origem_automatica_nao_expoe_cancelar(self):
        titulo=self._titulo(origem=TituloFinanceiro.OrigemTipo.COMPRA_RECEBIMENTO)
        url=reverse("financeiro:titulo_detalhe",kwargs={"titulo_uuid":titulo.uuid})+f"?escopo=loja&loja={self.loja.pk}"
        r=self.client.get(url)
        self.assertEqual(r.status_code,200)
        self.assertNotContains(r,reverse("financeiro:titulo_cancelar",kwargs={"titulo_uuid":titulo.uuid}))


from financeiro.models import BaixaFinanceira, FechamentoGerencial, ParcelaFinanceira
from financeiro.services import registrar_baixa_financeira, estornar_baixa_financeira


class F26Z36AFechamentoBaixaEstornoWebTests(F26Z35CancelamentoWebFuncionalTests):
    def test_competencia_fechada_bloqueia_get_e_oculta_cancelar_no_detalhe(self):
        titulo = self._titulo()
        FechamentoGerencial.objects.create(
            matriz=self.matriz,
            competencia_ano=2026,
            competencia_mes=10,
            status=FechamentoGerencial.Status.FECHADO,
            fechado_por=self.user,
        )
        r = self.client.get(self._url(titulo))
        self.assertEqual(r.status_code, 403)

        detalhe = reverse(
            "financeiro:titulo_detalhe",
            kwargs={"titulo_uuid": titulo.uuid},
        ) + f"?escopo=loja&loja={self.loja.pk}"
        r = self.client.get(detalhe)
        self.assertEqual(r.status_code, 200)
        self.assertNotContains(
            r,
            reverse("financeiro:titulo_cancelar", kwargs={"titulo_uuid": titulo.uuid}),
        )

    def test_baixa_ativa_mantem_confirmacao_motivo_e_bloqueia_cancelamento(self):
        titulo = self._titulo()
        parcela = titulo.parcelas.get(numero=1)
        registrar_baixa_financeira(
            parcela=parcela,
            valor=Decimal("100.00"),
            data=date(2026, 10, 24),
            chave_idempotencia="f26z36a-baixa-1",
            usuario=self.user,
        )
        motivo = "Correcao controlada apos baixa"
        r = self.client.post(self._url(titulo), {"motivo": motivo})
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, motivo)
        titulo.refresh_from_db()
        self.assertNotEqual(titulo.status, TituloFinanceiro.Status.CANCELADO)
        self.assertEqual(
            BaixaFinanceira.objects.filter(parcela__titulo=titulo).count(), 1
        )

    def test_estorno_integral_explicito_permite_cancelar_e_preserva_eventos(self):
        titulo = self._titulo()
        parcela = titulo.parcelas.get(numero=1)
        baixa = registrar_baixa_financeira(
            parcela=parcela,
            valor=Decimal("100.00"),
            data=date(2026, 10, 24),
            chave_idempotencia="f26z36a-baixa-2",
            usuario=self.user,
        )
        estorno = estornar_baixa_financeira(
            baixa=baixa,
            valor=Decimal("100.00"),
            data=date(2026, 10, 25),
            chave_idempotencia="f26z36a-estorno-2",
            usuario=self.user,
        )
        ids_antes = list(
            BaixaFinanceira.objects.filter(parcela__titulo=titulo)
            .order_by("pk")
            .values_list("pk", flat=True)
        )
        r = self.client.post(
            self._url(titulo),
            {"motivo": "Baixa integralmente estornada; cancelar titulo incorreto"},
        )
        self.assertEqual(r.status_code, 302)
        titulo.refresh_from_db()
        parcela.refresh_from_db()
        self.assertEqual(titulo.status, TituloFinanceiro.Status.CANCELADO)
        self.assertEqual(parcela.status, ParcelaFinanceira.Status.CANCELADO)
        ids_depois = list(
            BaixaFinanceira.objects.filter(parcela__titulo=titulo)
            .order_by("pk")
            .values_list("pk", flat=True)
        )
        self.assertEqual(ids_depois, ids_antes)
        self.assertTrue(BaixaFinanceira.objects.filter(pk=baixa.pk).exists())
        self.assertEqual(
            BaixaFinanceira.objects.get(pk=estorno.pk).baixa_estornada_id,
            baixa.pk,
        )
