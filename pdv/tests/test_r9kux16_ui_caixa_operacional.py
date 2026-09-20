from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from accounts.models import PermissaoUsuario
from empresas.models import Loja, Matriz
from pdv.models import Caixa, MovimentacaoCaixa, SessaoCaixa
from pdv.choices import TipoMovimentacaoCaixa
from pdv.constants import PERMISSAO_PDV_SUPRIMENTO, PERMISSAO_PDV_SANGRIA


class R9KUX16UiCaixaOperacionalTests(TestCase):
    def setUp(self):
        self.matriz=Matriz.objects.create(nome="Matriz UI16")
        self.loja=Loja.objects.create(matriz=self.matriz,nome="Loja UI16")
        U=get_user_model()
        self.user=U.objects.create_user(username="ui16",password="x",matriz=self.matriz)
        self.user.lojas.add(self.loja)
        self.caixa=Caixa.objects.create(matriz=self.matriz,loja=self.loja,codigo="UI16",nome="Caixa UI16")
        self.sessao=SessaoCaixa.objects.create(caixa=self.caixa,operador_abertura=self.user,valor_abertura=Decimal("0.00"))
        self.client.force_login(self.user)

    def grant(self, codigo):
        PermissaoUsuario.objects.create(usuario=self.user, permissao=codigo)

    def test_suprimento_exige_permissao(self):
        r=self.client.get(reverse("pdv:suprimento_caixa"))
        self.assertEqual(r.status_code,403)

    def test_suprimento_na_sessao_propria_aberta(self):
        self.grant(PERMISSAO_PDV_SUPRIMENTO)
        r=self.client.post(reverse("pdv:suprimento_caixa"),{"valor":"15,00","observacao":"Suprimento teste"})
        self.assertEqual(r.status_code,302)
        m=MovimentacaoCaixa.objects.get(sessao_caixa=self.sessao,tipo=TipoMovimentacaoCaixa.SUPRIMENTO)
        self.assertEqual(m.valor,Decimal("15.00"))
        self.assertEqual(m.operador,self.user)

    def test_sangria_exige_permissao(self):
        r=self.client.get(reverse("pdv:sangria_caixa"))
        self.assertEqual(r.status_code,403)

    def test_sangria_insuficiente_via_ui_nao_persiste(self):
        self.grant(PERMISSAO_PDV_SANGRIA)
        r=self.client.post(reverse("pdv:sangria_caixa"),{"valor":"1,00","observacao":"Nao pode"})
        self.assertEqual(r.status_code,200)
        self.assertFalse(MovimentacaoCaixa.objects.filter(sessao_caixa=self.sessao,tipo=TipoMovimentacaoCaixa.SANGRIA).exists())

    def test_sem_sessao_propria_nao_movimenta(self):
        self.grant(PERMISSAO_PDV_SUPRIMENTO)
        self.sessao.delete()
        r=self.client.post(reverse("pdv:suprimento_caixa"),{"valor":"15,00"})
        self.assertEqual(r.status_code,302)
        self.assertFalse(MovimentacaoCaixa.objects.filter(tipo=TipoMovimentacaoCaixa.SUPRIMENTO).exists())