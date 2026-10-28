from datetime import date
from decimal import Decimal

from django.core.exceptions import PermissionDenied
from django.test import TestCase

from accounts.models import PermissaoUsuario, Usuario
from accounts.permissions import PERMISSAO_FINANCEIRO_EDITAR_LANCAMENTO
from empresas.models import Loja, Matriz
from financeiro.models import PlanoConta
from financeiro.services import criar_lancamento_manual, atualizar_lancamento_manual


class F26Z16BDestinoEscopoEdicaoRED(TestCase):
    def setUp(self):
        self.matriz=Matriz.objects.create(nome="Matriz Z16B")
        self.loja_a=Loja.objects.create(matriz=self.matriz,nome="Loja A Z16B")
        self.loja_b=Loja.objects.create(matriz=self.matriz,nome="Loja B Z16B")
        self.plano=PlanoConta.objects.create(
            matriz=self.matriz,codigo="Z16B",nome="Despesa Z16B",
            natureza="DESPESA",classificacao_dre="DESPESA_OPERACIONAL",
            tipo=PlanoConta.Tipo.ANALITICA,aceita_lancamento=True,
        )
        self.admin=Usuario.objects.create_user(
            username="admz16b",password="x",perfil=Usuario.PERFIL_ADMIN_LOJA,matriz=self.matriz
        )
        self.admin.lojas.add(self.loja_a,self.loja_b)
        self.operador=Usuario.objects.create_user(
            username="opz16b",password="x",perfil=Usuario.PERFIL_OPERADOR,matriz=self.matriz
        )
        self.operador.lojas.add(self.loja_a)
        PermissaoUsuario.objects.create(
            usuario=self.operador,permissao=PERMISSAO_FINANCEIRO_EDITAR_LANCAMENTO
        )
        self.titulo=criar_lancamento_manual(
            matriz=self.matriz,loja=self.loja_a,natureza="PAGAR",
            chave_idempotencia="z16b",descricao="Titulo Z16B",
            data_emissao=date(2026,11,1),
            parcelas=[{"numero":1,"vencimento":date(2026,11,20),"valor":Decimal("100.00")}],
            plano_conta=self.plano,centro_custo=None,entidade_nome="Fornecedor",
            documento_referencia="DOC-Z16B",data_competencia=date(2026,11,1),
            valor_bruto=Decimal("100.00"),valor_desconto=Decimal("0.00"),
            valor_juros=Decimal("0.00"),observacao="Original",
            usuario=self.admin,request=None,
        )

    def _editar(self, loja):
        return atualizar_lancamento_manual(
            titulo=self.titulo,usuario=self.operador,request=None,
            loja=loja,natureza="PAGAR",plano_conta=self.plano,centro_custo=None,
            entidade_nome="Fornecedor",documento_referencia="DOC-Z16B",
            descricao="Titulo Z16B",data_emissao=date(2026,11,1),
            data_competencia=date(2026,11,1),valor_bruto=Decimal("100.00"),
            valor_desconto=Decimal("0.00"),valor_juros=Decimal("0.00"),
            observacao="Original",
            parcelas=[{"numero":1,"vencimento":date(2026,11,20),"valor":Decimal("100.00")}],
        )

    def test_01_operador_nao_pode_mover_titulo_para_loja_irma_nao_atribuida(self):
        with self.assertRaises(PermissionDenied):
            self._editar(self.loja_b)
        self.titulo.refresh_from_db()
        self.assertEqual(self.titulo.loja_id,self.loja_a.id)

    def test_02_operador_pode_manter_titulo_na_propria_loja(self):
        self._editar(self.loja_a)
        self.titulo.refresh_from_db()
        self.assertEqual(self.titulo.loja_id,self.loja_a.id)