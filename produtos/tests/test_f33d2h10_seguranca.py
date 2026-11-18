from unittest.mock import patch
from django.test import TestCase, RequestFactory, Client
from django.contrib.auth import get_user_model
from django.contrib.messages.storage.fallback import FallbackStorage
from django.core.exceptions import ValidationError
from django.urls import reverse
from empresas.models import Matriz
from produtos.models.logistica import (ApresentacaoProduto, ModeloCaixaExpedicao, CapacidadeReferenciaCaixa, AuditoriaCadastroLogistico)
from produtos.views import logistica as views

class F33D2H10SegurancaTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.a=Matriz.objects.create(nome='F33H10 Matriz A')
        cls.b=Matriz.objects.create(nome='F33H10 Matriz B')
        cls.caixa=ModeloCaixaExpedicao.objects.create(matriz=cls.a,nome='Caixa protegida',largura_cm=30,altura_cm=30,comprimento_cm=30)
        cls.ap=ApresentacaoProduto.objects.create(matriz=cls.a,nome='Pote protegido',tipo='POTE')
        cls.cap=CapacidadeReferenciaCaixa.objects.create(matriz=cls.a,caixa=cls.caixa,apresentacao=cls.ap,quantidade=4)
        cls.caixa_b=ModeloCaixaExpedicao.objects.create(matriz=cls.b,nome='Caixa matriz B',largura_cm=20,altura_cm=20,comprimento_cm=20)

    def _post(self,tipo,pk,acao,matriz=None):
        req=RequestFactory().post('/produtos/logistica/%s/%s/acao/'%(tipo,pk),{'acao':acao})
        req.user=get_user_model()()  # auditoria permite usuario nulo? mock abaixo
        req.session={}
        req._messages=FallbackStorage(req)
        # Testa o nucleo real da view, sem decorators; a autorizacao HTTP e verificada separadamente.
        from inspect import unwrap
        with patch.object(views,'get_contexto_operacional_usuario',return_value={'matriz':matriz or self.a}), patch.object(views,'_audit') as audit:
            response=unwrap(views.acao_logistica)(req,tipo,pk)
            return response,audit

    def test_caixa_com_capacidade_nao_exclui(self):
        _,audit=self._post('caixas',self.caixa.pk,'excluir')
        self.assertTrue(ModeloCaixaExpedicao.objects.filter(pk=self.caixa.pk).exists())
        self.assertTrue(CapacidadeReferenciaCaixa.objects.filter(pk=self.cap.pk).exists())
        audit.assert_not_called()

    def test_apresentacao_com_capacidade_nao_exclui(self):
        _,audit=self._post('apresentacoes',self.ap.pk,'excluir')
        self.assertTrue(ApresentacaoProduto.objects.filter(pk=self.ap.pk).exists())
        self.assertTrue(CapacidadeReferenciaCaixa.objects.filter(pk=self.cap.pk).exists())
        audit.assert_not_called()

    def test_caixa_sem_dependencias_exclui_e_audita(self):
        caixa=ModeloCaixaExpedicao.objects.create(matriz=self.a,nome='Temporaria',largura_cm=10,altura_cm=10,comprimento_cm=10)
        _,audit=self._post('caixas',caixa.pk,'excluir')
        self.assertFalse(ModeloCaixaExpedicao.objects.filter(pk=caixa.pk).exists())
        self.assertEqual(audit.call_args.args[4],'EXCLUSAO')

    def test_inativacao_reativacao_e_auditoria(self):
        _,audit=self._post('caixas',self.caixa.pk,'inativar')
        self.caixa.refresh_from_db()
        self.assertFalse(self.caixa.ativo)
        self.assertEqual(audit.call_args.args[4],'INATIVAR')
        _,audit=self._post('caixas',self.caixa.pk,'reativar')
        self.caixa.refresh_from_db()
        self.assertTrue(self.caixa.ativo)
        self.assertEqual(audit.call_args.args[4],'REATIVAR')

    def test_outra_matriz_nao_altera(self):
        from django.http import Http404
        with self.assertRaises(Http404):
            self._post('caixas',self.caixa_b.pk,'excluir')
        self.assertTrue(ModeloCaixaExpedicao.objects.filter(pk=self.caixa_b.pk).exists())

    def test_get_nao_altera(self):
        from inspect import unwrap
        req=RequestFactory().get('/teste/')
        response=unwrap(views.acao_logistica)(req,'caixas',self.caixa.pk)
        self.assertEqual(response.status_code,405)

    def test_anonimo_bloqueado_na_rota_real(self):
        response=Client().post(reverse('produtos:logistica_acao',kwargs={'tipo':'caixas','item_id':self.caixa.pk}),{'acao':'excluir'})
        self.assertIn(response.status_code,(302,403))
        self.assertTrue(ModeloCaixaExpedicao.objects.filter(pk=self.caixa.pk).exists())

    def test_matriz_inconsistente_bloqueada_no_modelo(self):
        with self.assertRaises(ValidationError):
            CapacidadeReferenciaCaixa.objects.create(matriz=self.b,caixa=self.caixa,apresentacao=self.ap,quantidade=1)
