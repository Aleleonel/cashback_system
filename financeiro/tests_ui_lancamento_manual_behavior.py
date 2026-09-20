from datetime import date
from decimal import Decimal
from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import NoReverseMatch, reverse

from accounts.models import Usuario
from empresas.models import Loja, Matriz
from financeiro.models import CentroCusto, PlanoConta, TituloFinanceiro


class FinanceiroUiLancamentoManualBehaviorTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.matriz_a = Matriz.objects.create(nome="Matriz R9H A", cnpj="91919191000191")
        cls.matriz_b = Matriz.objects.create(nome="Matriz R9H B", cnpj="92929292000191")
        cls.loja_a = Loja.objects.create(matriz=cls.matriz_a, nome="Loja R9H A")
        cls.loja_b = Loja.objects.create(matriz=cls.matriz_b, nome="Loja R9H B")
        cls.master = Usuario.objects.create_user(username="r9h_master", password="Senha123!", matriz=cls.matriz_a, perfil=Usuario.PERFIL_MASTER)
        cls.operador = Usuario.objects.create_user(username="r9h_operador", password="Senha123!", matriz=cls.matriz_a, perfil=Usuario.PERFIL_OPERADOR)
        cls.plano_a = PlanoConta.objects.create(matriz=cls.matriz_a, codigo="9.1", nome="Plano R9H A", tipo=PlanoConta.Tipo.ANALITICA, aceita_lancamento=True, ativo=True)
        cls.plano_b = PlanoConta.objects.create(matriz=cls.matriz_b, codigo="9.2", nome="Plano R9H B", tipo=PlanoConta.Tipo.ANALITICA, aceita_lancamento=True, ativo=True)
        cls.centro_a = CentroCusto.objects.create(matriz=cls.matriz_a, codigo="R9HA", nome="Centro R9H A", ativo=True)
        cls.centro_b = CentroCusto.objects.create(matriz=cls.matriz_b, codigo="R9HB", nome="Centro R9H B", ativo=True)

    def _url(self):
        try:
            return reverse("financeiro:lancamento_manual")
        except NoReverseMatch as exc:
            self.fail(f"Rota financeira esperada ausente: financeiro:lancamento_manual. Detalhe: {exc}")

    def _payload(self, **overrides):
        data = {
            "natureza": TituloFinanceiro.Natureza.PAGAR,
            "chave_idempotencia": "22222222-2222-4222-8222-222222222222",
            "loja": str(self.loja_a.pk),
            "plano_conta": str(self.plano_a.pk),
            "centro_custo": str(self.centro_a.pk),
            "entidade_nome": "Fornecedor R9H",
            "documento_referencia": "DOC-R9H",
            "data_emissao": "2026-09-16",
            "data_competencia": "2026-09-01",
            "data_vencimento": "2026-10-10",
            "valor_bruto": "100.00",
            "valor_desconto": "10.00",
            "valor_juros": "5.00",
            "numero_parcelas": "3",
            "observacao": "Teste R9H",
        }
        data.update(overrides)
        return data

    def test_get_filtra_loja_plano_e_centro_por_matriz(self):
        self.client.force_login(self.master)
        response = self.client.get(self._url())
        self.assertEqual(response.status_code, 200)
        form = response.context["form"]
        self.assertQuerySetEqual(form.fields["loja"].queryset, [self.loja_a])
        self.assertQuerySetEqual(form.fields["plano_conta"].queryset, [self.plano_a])
        self.assertQuerySetEqual(form.fields["centro_custo"].queryset, [self.centro_a])
        self.assertNotIn(self.loja_b, form.fields["loja"].queryset)
        self.assertNotIn(self.plano_b, form.fields["plano_conta"].queryset)
        self.assertNotIn(self.centro_b, form.fields["centro_custo"].queryset)

    @patch("financeiro.views.criar_lancamento_manual")
    def test_post_delega_service_com_matriz_e_parcelas_exatas(self, service):
        service.return_value = type("TituloFake", (), {"uuid": "11111111-1111-4111-8111-111111111111"})()
        self.client.force_login(self.master)
        response = self.client.post(self._url(), self._payload())
        self.assertIn(response.status_code, (302, 303))
        kwargs = service.call_args.kwargs
        self.assertEqual(kwargs["matriz"], self.matriz_a)
        self.assertEqual(kwargs["loja"], self.loja_a)
        self.assertEqual(kwargs["plano_conta"], self.plano_a)
        self.assertEqual(kwargs["centro_custo"], self.centro_a)
        self.assertEqual(kwargs["data_competencia"], date(2026, 9, 1))
        self.assertEqual(kwargs["valor_bruto"], Decimal("100.00"))
        self.assertEqual(kwargs["valor_desconto"], Decimal("10.00"))
        self.assertEqual(kwargs["valor_juros"], Decimal("5.00"))
        parcelas = kwargs["parcelas"]
        self.assertEqual([p["numero"] for p in parcelas], [1, 2, 3])
        self.assertEqual(parcelas[0]["vencimento"], date(2026, 10, 10))
        self.assertEqual(sum((p["valor"] for p in parcelas), Decimal("0.00")), Decimal("95.00"))

    @patch("financeiro.views.criar_lancamento_manual")
    def test_post_cross_tenant_nao_chama_service(self, service):
        self.client.force_login(self.master)
        response = self.client.post(self._url(), self._payload(loja=str(self.loja_b.pk), plano_conta=str(self.plano_b.pk), centro_custo=str(self.centro_b.pk)))
        self.assertEqual(response.status_code, 200)
        service.assert_not_called()

    @patch("financeiro.views.criar_lancamento_manual")
    def test_validation_error_do_service_volta_ao_form(self, service):
        service.side_effect = ValidationError({"parcelas": "A soma das parcelas deve ser igual ao valor final."})
        self.client.force_login(self.master)
        response = self.client.post(self._url(), self._payload())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "A soma das parcelas deve ser igual ao valor final.")

    @patch("financeiro.views.criar_lancamento_manual")
    def test_usuario_sem_gerenciar_nao_cria(self, service):
        self.client.force_login(self.operador)
        response = self.client.post(self._url(), self._payload())
        self.assertIn(response.status_code, (302, 403, 404))
        service.assert_not_called()