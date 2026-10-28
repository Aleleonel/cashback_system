from datetime import date
from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from accounts.models import Usuario, PermissaoUsuario
from accounts.permissions import PERMISSAO_FINANCEIRO_EDITAR_LANCAMENTO
from empresas.models import Matriz, Loja
from financeiro.models import TituloFinanceiro, ParcelaFinanceira, FechamentoGerencial
class F26Z24ParidadeFechamentoUITest(TestCase):
    def setUp(self):
        self.matriz=Matriz.objects.create(nome="Matriz Z24");self.loja=Loja.objects.create(matriz=self.matriz,nome="Loja Z24")
        self.user=Usuario.objects.create_user(username="z24",password="x",matriz=self.matriz,perfil="admin_loja");self.user.lojas.add(self.loja);PermissaoUsuario.objects.create(usuario=self.user, permissao=PERMISSAO_FINANCEIRO_EDITAR_LANCAMENTO)
        self.t=TituloFinanceiro.objects.create(matriz=self.matriz,loja=self.loja,natureza="PAGAR",origem_tipo="MANUAL",status="ABERTO",data_emissao=date(2026,10,1),data_competencia=date(2026,10,15),valor_bruto=Decimal("10.00"),valor_desconto=0,valor_juros=0,valor_original=Decimal("10.00"),descricao="Z24")
        ParcelaFinanceira.objects.create(titulo=self.t,numero=1,vencimento=date(2026,10,20),valor_original=Decimal("10.00"));self.client.force_login(self.user)
    def detail(self): return reverse("financeiro:titulo_detalhe",kwargs={"titulo_uuid":self.t.uuid})+"?escopo=loja&loja="+str(self.loja.pk)
    def edit(self): return reverse("financeiro:titulo_editar",kwargs={"titulo_uuid":self.t.uuid})+"?escopo=loja&loja="+str(self.loja.pk)
    def test_aberta(self):
        self.assertContains(self.client.get(self.detail()),"Editar t\u00edtulo");self.assertEqual(self.client.get(self.edit()).status_code,200)
    def test_fechada_oculta(self):
        FechamentoGerencial.objects.create(matriz=self.matriz,competencia_ano=2026,competencia_mes=10,status="FECHADO");self.assertNotContains(self.client.get(self.detail()),"Editar tÃ­tulo")
    def test_fechada_bloqueia_get(self):
        FechamentoGerencial.objects.create(matriz=self.matriz,competencia_ano=2026,competencia_mes=10,status="FECHADO");self.assertIn(self.client.get(self.edit()).status_code,(403,404))