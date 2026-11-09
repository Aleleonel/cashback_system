"""F32P4C: contrato HTTP real para consolidacao nao fiscal do Atacado."""
import json
from decimal import Decimal
from django.test import Client
from django.urls import reverse
from atacado.tests.test_f32p3u_integracao_banco import F32P3UIntegracaoBancoTests
from atacado.models import StatusPedidoAtacado
from estoque.models import ReservaEstoque
from pdv.models import Venda

class F32P4CHttpTests(F32P3UIntegracaoBancoTests):
    # Nao herdar os testes transacionais: reutilizar apenas a fixture.
    def url(self, pedido):
        return reverse('atacado:pedido_consolidar_pdv', args=[pedido.pk])

    def fixture(self):
        pedido, sessao, usuario, pagamentos = self.preparar()
        usuario.perfil = 'operador'
        usuario.ativo = True
        usuario.save(update_fields=['perfil', 'ativo'])
        self.client.force_login(usuario)
        return pedido, sessao, usuario, pagamentos

    def post(self, pedido, pagamentos):
        return self.client.post(self.url(pedido), data=json.dumps({'pagamentos': pagamentos}), content_type='application/json')

    def test_post_valido_cria_venda_e_idempotencia_http(self):
        pedido, sessao, usuario, pagamentos = self.fixture()
        resposta = self.post(pedido, pagamentos)
        self.assertEqual(resposta.status_code, 200, resposta.content[:800])
        self.assertTrue(resposta.json()['ok'])
        pedido.refresh_from_db()
        self.assertEqual(pedido.status, StatusPedidoAtacado.FINALIZADO)
        self.assertEqual(Venda.objects.count(), 1)
        self.assertEqual(Venda.objects.get().sessao_caixa_id, sessao.pk)
        # A view pode optar por 409 na repeticao, mas nunca duplicar a venda.
        segunda = self.post(pedido, pagamentos)
        self.assertIn(segunda.status_code, (200, 409), segunda.content[:800])
        self.assertEqual(Venda.objects.count(), 1)

    def test_get_nao_finaliza(self):
        pedido, _, _, _ = self.fixture()
        resposta = self.client.get(self.url(pedido))
        self.assertEqual(resposta.status_code, 405)
        self.assertEqual(Venda.objects.count(), 0)

    def test_sem_sessao_aberta_bloqueia(self):
        pedido, sessao, _, pagamentos = self.fixture()
        sessao.delete()
        resposta = self.post(pedido, pagamentos)
        self.assertEqual(resposta.status_code, 409, resposta.content[:800])
        self.assertEqual(Venda.objects.count(), 0)

    def test_pagamentos_ausentes_bloqueia(self):
        pedido, _, _, _ = self.fixture()
        resposta = self.post(pedido, [])
        self.assertEqual(resposta.status_code, 400, resposta.content[:800])
        self.assertEqual(Venda.objects.count(), 0)

    def test_superuser_nao_opera_caixa(self):
        pedido, _, _, pagamentos = self.fixture()
        usuario = __import__('django.contrib.auth', fromlist=['get_user_model']).get_user_model().objects.create_superuser(username='f32p4c_super', password='F32P4C!Test123', email='f32p4c@example.test')
        self.client.force_login(usuario)
        resposta = self.post(pedido, pagamentos)
        self.assertEqual(resposta.status_code, 403, resposta.content[:800])
        self.assertEqual(Venda.objects.count(), 0)

    def test_outro_operador_sem_sessao_nao_usa_caixa_alheio(self):
        pedido, _, _, pagamentos = self.fixture()
        usuario = __import__('django.contrib.auth', fromlist=['get_user_model']).get_user_model().objects.create_user(username='f32p4c_outro', password='F32P4C!Test123', matriz=self.matriz)
        usuario.perfil = 'operador'
        usuario.ativo = True
        usuario.save(update_fields=['perfil', 'ativo'])
        usuario.lojas.add(self.loja)
        self.client.force_login(usuario)
        resposta = self.post(pedido, pagamentos)
        self.assertEqual(resposta.status_code, 409, resposta.content[:800])
        self.assertEqual(Venda.objects.count(), 0)
