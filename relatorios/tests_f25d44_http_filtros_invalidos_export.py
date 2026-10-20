from unittest.mock import patch
from django.test import TestCase
from django.urls import reverse
from accounts.models import Usuario
from empresas.models import Matriz, Loja, StatusOperacional

class DREHTTPFiltrosInvalidosExportTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.matriz=Matriz.objects.create(nome="F25D44 Matriz",cnpj="44.444.444/0001-44")
        cls.loja=Loja.objects.create(matriz=cls.matriz,nome="F25D44 Loja",cnpj="44.444.444/0002-25",status=StatusOperacional.ATIVA)
        cls.admin=Usuario.objects.create_user(username="f25d44_admin",password="Teste@123",matriz=cls.matriz,perfil="admin_loja")
        cls.admin.lojas.add(cls.loja)
        cls.superuser=Usuario.objects.create_superuser(username="f25d44_root",password="Teste@123",email="f25d44@example.com")

    def test_html_data_invalida_200_preserva_input_e_nao_apura(self):
        self.client.force_login(self.admin)
        with patch("relatorios.views.apurar_dre") as apurar, patch("relatorios.views.apurar_evolucao_mensal") as evoluir:
            r=self.client.get(reverse("relatorios:dre"),{"data_inicio":"2026-99-99","data_fim":"2026-10-31"})
        self.assertEqual(r.status_code,200);self.assertContains(r,"2026-99-99");self.assertContains(r,"alert-danger")
        self.assertIsNone(r.context["resultado"]);self.assertFalse(r.context["filtros_validos"]);apurar.assert_not_called();evoluir.assert_not_called()

    def test_html_periodo_invertido_200_nao_apura(self):
        self.client.force_login(self.admin)
        with patch("relatorios.views.apurar_dre") as apurar, patch("relatorios.views.apurar_evolucao_mensal") as evoluir:
            r=self.client.get(reverse("relatorios:dre"),{"data_inicio":"2026-10-31","data_fim":"2026-10-01"})
        self.assertEqual(r.status_code,200);self.assertFalse(r.context["filtros_validos"]);self.assertIsNone(r.context["resultado"]);apurar.assert_not_called();evoluir.assert_not_called()

    def test_pdf_data_invalida_400_e_nao_apura(self):
        self.client.force_login(self.admin)
        with patch("relatorios.views.apurar_dre") as apurar:
            r=self.client.get(reverse("relatorios:exportar_dre_pdf"),{"data_inicio":"invalida","data_fim":"2026-10-31"})
        self.assertEqual(r.status_code,400);self.assertTrue(r["Content-Type"].startswith("text/plain"));apurar.assert_not_called()

    def test_xlsx_periodo_invertido_400_e_nao_apura(self):
        self.client.force_login(self.admin)
        with patch("relatorios.views.apurar_dre") as apurar:
            r=self.client.get(reverse("relatorios:exportar_dre_xlsx"),{"data_inicio":"2026-10-31","data_fim":"2026-10-01"})
        self.assertEqual(r.status_code,400);self.assertTrue(r["Content-Type"].startswith("text/plain"));apurar.assert_not_called()

    def test_superuser_sem_matriz_html_neutro_e_exports_400(self):
        self.client.force_login(self.superuser)
        with patch("relatorios.views.apurar_dre") as apurar:
            html=self.client.get(reverse("relatorios:dre"));pdf=self.client.get(reverse("relatorios:exportar_dre_pdf"));xlsx=self.client.get(reverse("relatorios:exportar_dre_xlsx"))
        self.assertEqual(html.status_code,200);self.assertFalse(html.context["filtros_validos"]);self.assertIsNone(html.context["resultado"])
        self.assertEqual(pdf.status_code,400);self.assertEqual(xlsx.status_code,400);apurar.assert_not_called()

    def test_superuser_matriz_inexistente_nao_faz_fallback(self):
        self.client.force_login(self.superuser)
        with patch("relatorios.views.apurar_dre") as apurar:
            r=self.client.get(reverse("relatorios:dre"),{"matriz":"999999"})
        self.assertEqual(r.status_code,200);self.assertIsNone(r.context["matriz"]);self.assertFalse(r.context["filtros_validos"]);self.assertIsNone(r.context["resultado"]);apurar.assert_not_called()

    def test_fabricaadm_ignora_matriz_estrangeira(self):
        outra=Matriz.objects.create(nome="F25D44 Outra",cnpj="55.555.555/0001-55")
        self.client.force_login(self.admin)
        with patch("relatorios.views.apurar_dre") as apurar, patch("relatorios.views.apurar_evolucao_mensal",return_value=[]):
            apurar.return_value={"resultado":object(),"analise_vertical":{},"drilldown":{},"comparativo":None}
            r=self.client.get(reverse("relatorios:dre"),{"matriz":str(outra.pk),"data_inicio":"2026-10-01","data_fim":"2026-10-31"})
        self.assertEqual(r.status_code,200);self.assertEqual(r.context["matriz"].pk,self.matriz.pk);self.assertEqual(apurar.call_args.kwargs["matriz"].pk,self.matriz.pk)

    def test_superuser_matriz_valida_calcula_escopo_explicito(self):
        self.client.force_login(self.superuser)
        with patch("relatorios.views.apurar_dre") as apurar, patch("relatorios.views.apurar_evolucao_mensal",return_value=[]):
            apurar.return_value={"resultado":object(),"analise_vertical":{},"drilldown":{},"comparativo":None}
            r=self.client.get(reverse("relatorios:dre"),{"matriz":str(self.matriz.pk),"data_inicio":"2026-10-01","data_fim":"2026-10-31"})
        self.assertEqual(r.status_code,200);self.assertTrue(r.context["filtros_validos"]);self.assertEqual(apurar.call_args.kwargs["matriz"].pk,self.matriz.pk)
