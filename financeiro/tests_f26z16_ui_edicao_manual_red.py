from datetime import date
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from accounts.models import PermissaoUsuario, Usuario
from accounts.permissions import PERMISSAO_FINANCEIRO_EDITAR_LANCAMENTO, PERMISSAO_FINANCEIRO_VISUALIZAR
from empresas.models import Loja, Matriz
from financeiro.models import PlanoConta, TituloFinanceiro
from financeiro.services import criar_lancamento_manual


class F26Z16UIEdicaoManualRED(TestCase):
    def setUp(self):
        self.matriz = Matriz.objects.create(nome="Matriz Z16")
        self.loja_a = Loja.objects.create(matriz=self.matriz, nome="Loja A Z16")
        self.loja_b = Loja.objects.create(matriz=self.matriz, nome="Loja B Z16")
        self.plano = PlanoConta.objects.create(
            matriz=self.matriz, codigo="Z16", nome="Despesa Z16",
            natureza="DESPESA", classificacao_dre="DESPESA_OPERACIONAL",
            tipo=PlanoConta.Tipo.ANALITICA, aceita_lancamento=True,
        )
        self.operador = Usuario.objects.create_user(
            username="opz16", password="x", perfil=Usuario.PERFIL_OPERADOR,
            matriz=self.matriz,
        )
        self.operador.lojas.add(self.loja_a)
        PermissaoUsuario.objects.create(
            usuario=self.operador, permissao=PERMISSAO_FINANCEIRO_EDITAR_LANCAMENTO
        )
        PermissaoUsuario.objects.create(
            usuario=self.operador, permissao=PERMISSAO_FINANCEIRO_VISUALIZAR
        )
        self.admin = Usuario.objects.create_user(
            username="admz16", password="x", perfil=Usuario.PERFIL_ADMIN_LOJA,
            matriz=self.matriz,
        )
        self.admin.lojas.add(self.loja_a, self.loja_b)
        self.titulo = criar_lancamento_manual(
            matriz=self.matriz, loja=self.loja_a, natureza="PAGAR",
            chave_idempotencia="z16-titulo", descricao="Titulo Z16",
            data_emissao=date(2026, 11, 1),
            parcelas=[{"numero": 1, "vencimento": date(2026, 11, 20), "valor": Decimal("100.00")}],
            plano_conta=self.plano, centro_custo=None, entidade_nome="Fornecedor Z16",
            documento_referencia="DOC-Z16", data_competencia=date(2026, 11, 1),
            valor_bruto=Decimal("100.00"), valor_desconto=Decimal("0.00"),
            valor_juros=Decimal("0.00"), observacao="Original",
            usuario=self.admin, request=None,
        )

    def _url(self):
        return reverse("financeiro:titulo_editar", kwargs={"titulo_uuid": self.titulo.uuid})

    def test_01_rota_edicao_existe(self):
        self.assertIn("/editar/", self._url())

    def test_02_sem_capability_nao_acessa(self):
        PermissaoUsuario.objects.filter(usuario=self.operador, permissao=PERMISSAO_FINANCEIRO_EDITAR_LANCAMENTO).delete()
        self.client.force_login(self.operador)
        r=self.client.get(self._url()+"?escopo=loja&loja="+str(self.loja_a.pk))
        self.assertIn(r.status_code,(403,404))

    def test_03_operador_com_capability_acessa_titulo_propria_loja(self):
        self.client.force_login(self.operador)
        r=self.client.get(self._url()+"?escopo=loja&loja="+str(self.loja_a.pk))
        self.assertEqual(r.status_code,200)
        self.assertContains(r,"DOC-Z16")

    def test_04_form_nao_oferece_loja_irma_ao_operador(self):
        self.client.force_login(self.operador)
        r=self.client.get(self._url()+"?escopo=loja&loja="+str(self.loja_a.pk))
        self.assertEqual(r.status_code,200)
        form=r.context["form"]
        self.assertIn(self.loja_a, list(form.fields["loja"].queryset))
        self.assertNotIn(self.loja_b, list(form.fields["loja"].queryset))

    def test_05_post_edita_via_servico_e_preserva_escopo_redirect(self):
        self.client.force_login(self.operador)
        data={
            "natureza":"PAGAR","loja":str(self.loja_a.pk),"plano_conta":str(self.plano.pk),
            "centro_custo":"","entidade_nome":"Fornecedor corrigido",
            "documento_referencia":"DOC-Z16-CORR","data_emissao":"2026-11-01",
            "data_competencia":"2026-11-01","data_vencimento":"2026-11-25",
            "valor_bruto":"120.00","valor_desconto":"0.00","valor_juros":"0.00",
            "numero_parcelas":"1","observacao":"Corrigido",
        }
        r=self.client.post(self._url()+"?escopo=loja&loja="+str(self.loja_a.pk),data)
        self.assertEqual(r.status_code,302)
        self.titulo.refresh_from_db()
        self.assertEqual(self.titulo.documento_referencia,"DOC-Z16-CORR")
        self.assertEqual(self.titulo.valor_original,Decimal("120.00"))
        self.assertIn("escopo=loja",r["Location"])
        self.assertIn("loja="+str(self.loja_a.pk),r["Location"])

    def test_06_detalhe_expoe_acao_editar_quando_autorizado(self):
        self.client.force_login(self.operador)
        url=reverse("financeiro:titulo_detalhe",kwargs={"titulo_uuid":self.titulo.uuid})
        r=self.client.get(url+"?escopo=loja&loja="+str(self.loja_a.pk))
        self.assertEqual(r.status_code,200)
        self.assertContains(r,self._url())

    def test_07_detalhe_nao_expoe_editar_sem_capability(self):
        PermissaoUsuario.objects.filter(usuario=self.operador, permissao=PERMISSAO_FINANCEIRO_EDITAR_LANCAMENTO).delete()
        self.client.force_login(self.operador)
        url=reverse("financeiro:titulo_detalhe",kwargs={"titulo_uuid":self.titulo.uuid})
        r=self.client.get(url+"?escopo=loja&loja="+str(self.loja_a.pk))
        self.assertEqual(r.status_code,200)
        self.assertNotContains(r,"/editar/")

    def test_08_titulo_com_baixa_nao_deve_ser_editavel_pela_ui(self):
        # Contrato de apresentacao: a UI deve refletir a mesma regra de mutabilidade do dominio.
        self.titulo.status=TituloFinanceiro.Status.LIQUIDADO
        self.titulo.save(update_fields=["status"])
        self.client.force_login(self.operador)
        r=self.client.get(self._url()+"?escopo=loja&loja="+str(self.loja_a.pk))
        self.assertIn(r.status_code,(403,404))