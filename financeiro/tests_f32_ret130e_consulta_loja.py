from django.test import TestCase
from django.urls import reverse
from accounts.models import PermissaoUsuario
from accounts.permissions import PERMISSAO_FINANCEIRO_VISUALIZAR
from financeiro.tests_f32p4h88q4e39f_pagamento_imediato import PagamentoImediatoF32Tests
from empresas.models import Loja


class ConsultaLojaRET130E(TestCase):
    @classmethod
    def setUpTestData(cls):
        PagamentoImediatoF32Tests.setUpTestData.__func__(cls)

    def setUp(self):
        self.client.force_login(self.operador)

    def test_sem_permissao_especifica_bloqueia_listagem_e_detalhe(self):
        self.assertEqual(self.client.get(reverse('financeiro:titulos')).status_code, 403)

    def test_permissao_especifica_habilita_somente_loja(self):
        PermissaoUsuario.objects.get_or_create(usuario=self.operador, permissao='financeiro.visualizar_lancamentos_loja')
        outra = Loja.objects.create(matriz=self.matriz, nome='Outra loja RET130E')
        response = self.client.get(reverse('financeiro:titulos'), {'escopo': 'consolidado', 'loja': str(outra.pk)})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loja'].pk, self.loja.pk)
        self.assertEqual(response.context['escopo'], 'loja')
        self.assertFalse(PermissaoUsuario.objects.filter(usuario=self.operador, permissao=PERMISSAO_FINANCEIRO_VISUALIZAR).exists())
        self.assertEqual(self.client.get(reverse('financeiro:painel')).status_code, 403)
        self.assertEqual(self.client.get(reverse('financeiro:repasse_novo')).status_code, 403)
