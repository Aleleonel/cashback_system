from datetime import date
from decimal import Decimal
from unittest.mock import patch
from django.core.exceptions import ValidationError
from auditoria.models import RegistroAuditoria
from financeiro.services import atualizar_lancamento_manual
from financeiro.tests_f26z3_edicao_manual_sem_baixa_red import F26Z3EdicaoManualSemBaixaRED

class F26Z5HardeningEdicaoManualRED(F26Z3EdicaoManualSemBaixaRED):
    def _kwargs(self):
        return dict(titulo=self.titulo, loja=self.loja, natureza=self.titulo.natureza,
            descricao="Correcao hardening", data_emissao=date(2026,11,10),
            parcelas=[{"numero":1,"vencimento":date(2026,11,30),"valor":Decimal("100.00")}],
            plano_conta=self.plano, centro_custo=None, entidade_nome="Fornecedor Z5",
            documento_referencia="Z5-001", data_competencia=date(2026,11,10),
            valor_bruto=Decimal("100.00"), valor_desconto=Decimal("0.00"),
            valor_juros=Decimal("0.00"), observacao="hardening", usuario=self.user)

    def test_09_falha_auditoria_desfaz_edicao_e_parcelas(self):
        antes=self.titulo.descricao
        pars=list(self.titulo.parcelas.values_list("numero","valor_original","vencimento"))
        with patch("financeiro.services.registrar_auditoria",side_effect=RuntimeError("falha auditoria")):
            with self.assertRaises(RuntimeError): atualizar_lancamento_manual(**self._kwargs())
        self.titulo.refresh_from_db()
        self.assertEqual(self.titulo.descricao,antes)
        self.assertEqual(list(self.titulo.parcelas.values_list("numero","valor_original","vencimento")),pars)

    def test_10_rejeita_soma_parcelas_divergente_sem_mutar(self):
        k=self._kwargs(); k["parcelas"]=[{"numero":1,"vencimento":date(2026,11,30),"valor":Decimal("99.00")}]
        antes=self.titulo.descricao
        with self.assertRaises(ValidationError): atualizar_lancamento_manual(**k)
        self.titulo.refresh_from_db(); self.assertEqual(self.titulo.descricao,antes)

    def test_11_rejeita_loja_de_outra_matriz(self):
        from empresas.models import Matriz, Loja
        m=Matriz.objects.create(nome="Outra matriz Z5"); loja=Loja.objects.create(matriz=m,nome="Outra loja Z5")
        k=self._kwargs(); k["loja"]=loja
        with self.assertRaises(ValidationError): atualizar_lancamento_manual(**k)

    def test_12_rejeita_plano_de_outra_matriz(self):
        from empresas.models import Matriz
        from financeiro.models import PlanoConta
        m=Matriz.objects.create(nome="Outra matriz plano Z5")
        plano=PlanoConta.objects.create(matriz=m,codigo="Z5",nome="Plano externo",natureza=PlanoConta.Natureza.DESPESA)
        k=self._kwargs(); k["plano_conta"]=plano
        with self.assertRaises(ValidationError): atualizar_lancamento_manual(**k)

    def test_13_rejeita_numero_parcela_duplicado(self):
        k=self._kwargs(); k["parcelas"]=[
            {"numero":1,"vencimento":date(2026,11,20),"valor":Decimal("50.00")},
            {"numero":1,"vencimento":date(2026,11,30),"valor":Decimal("50.00")}]
        with self.assertRaises(ValidationError): atualizar_lancamento_manual(**k)

    def test_14_rejeita_parcela_com_valor_nao_positivo(self):
        k=self._kwargs(); k["valor_bruto"]=Decimal("0.00")
        k["parcelas"]=[{"numero":1,"vencimento":date(2026,11,30),"valor":Decimal("0.00")}]
        with self.assertRaises(ValidationError): atualizar_lancamento_manual(**k)

    def test_15_auditoria_identifica_recurso_uuid_e_acao_editar(self):
        atualizar_lancamento_manual(**self._kwargs())
        self.assertEqual(RegistroAuditoria.objects.filter(matriz=self.matriz,
            acao=RegistroAuditoria.ACAO_EDITAR,recurso="financeiro.titulo",
            recurso_id=str(self.titulo.uuid)).count(),1)
