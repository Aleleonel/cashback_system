from unittest.mock import patch
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from empresas.models import Loja, Matriz


class RelatorioClientesViewTests(TestCase):
    def setUp(self):
        self.matriz = Matriz.objects.create(nome='Matriz View F2EA08')
        self.loja = Loja.objects.create(matriz=self.matriz, nome='Loja View F2EA08')
        User = get_user_model()
        self.user = User.objects.create_user(username='f2ea08', password='senha', perfil=User.PERFIL_OPERADOR, matriz=self.matriz)
        self.user.lojas.add(self.loja)
        self.client.force_login(self.user)
        self.url = reverse('relatorios:clientes')

    @patch('relatorios.views.get_contexto_operacional_usuario')
    @patch('relatorios.views.get_relatorio_clientes')
    def test_view_usa_matriz_operacional_e_selector(self, selector, contexto):
        contexto.return_value = {'matriz': self.matriz, 'loja': self.loja}
        selector.return_value = []
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        selector.assert_called_once()
        self.assertEqual(selector.call_args.kwargs['matriz'], self.matriz)
        self.assertIn('clientes', response.context)

    @patch('relatorios.views.get_contexto_operacional_usuario')
    @patch('relatorios.views.get_relatorio_clientes')
    def test_view_repassa_filtros_e_pagina_50(self, selector, contexto):
        contexto.return_value = {'matriz': self.matriz, 'loja': self.loja}
        selector.return_value = list(range(60))
        response = self.client.get(self.url, {'q':'Maria','ativo':'1','tipo_pessoa':'PF','loja':str(self.loja.id),'page':'2'})
        self.assertEqual(response.status_code, 200)
        kwargs = selector.call_args.kwargs
        self.assertEqual(kwargs['busca'], 'Maria')
        self.assertIs(kwargs['ativo'], True)
        self.assertEqual(kwargs['tipo_pessoa'], 'PF')
        self.assertEqual(kwargs['loja_id'], self.loja.id)
        page = response.context['clientes']
        self.assertEqual(page.paginator.per_page, 50)
        self.assertEqual(page.number, 2)
        self.assertEqual(len(page.object_list), 10)
