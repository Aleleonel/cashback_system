from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from empresas.models import Loja, Matriz
from configuracoes.models import FechamentoComissao

class FechamentoGlobalAtomicidadeTests(TestCase):
    def setUp(self):
        self.m=Matriz.objects.create(nome="Matriz Atomicidade")
        self.l1=Loja.objects.create(nome="Loja Atomicidade 1",matriz=self.m)
        self.l2=Loja.objects.create(nome="Loja Atomicidade 2",matriz=self.m)
        self.user=get_user_model().objects.create_user(username="f23_atomic",password="x",perfil="admin_loja",matriz=self.m,ativo=True)
        self.client.force_login(self.user)
        self.url=reverse("configuracoes:comissoes")

    def test_ui_expoe_opcao_todas_as_lojas(self):
        r=self.client.get(self.url)
        self.assertContains(r,'value="todas"')
        self.assertContains(r,"Todas as lojas")

    @patch("configuracoes.services_comissoes.fechar_comissoes_competencia")
    def test_falha_em_uma_loja_nao_e_mascarada(self, fechar):
        fechar.side_effect=[object(), RuntimeError("falha simulada")]
        with self.assertRaises(RuntimeError):
            self.client.post(self.url,{"acao":"fechamento_comissao","loja_fechamento_id":"todas","competencia_ano":"2026","competencia_mes":"9"})

    def test_global_real_e_atomico_no_nivel_da_orquestracao(self):
        # O contrato exige que os fechamentos do lote sejam uma unidade:
        # se a segunda loja falhar, snapshots criados pela primeira devem reverter.
        from configuracoes import services_comissoes
        original=services_comissoes.fechar_comissoes_competencia
        chamadas={"n":0}
        def falha_na_segunda(*,loja,ano,mes):
            chamadas["n"]+=1
            if chamadas["n"]==2:
                raise RuntimeError("falha simulada")
            return original(loja=loja,ano=ano,mes=mes)
        with patch("configuracoes.services_comissoes.fechar_comissoes_competencia",side_effect=falha_na_segunda):
            with self.assertRaises(RuntimeError):
                self.client.post(self.url,{"acao":"fechamento_comissao","loja_fechamento_id":"todas","competencia_ano":"2026","competencia_mes":"9"})
        self.assertFalse(FechamentoComissao.objects.filter(matriz=self.m,competencia_ano=2026,competencia_mes=9).exists())