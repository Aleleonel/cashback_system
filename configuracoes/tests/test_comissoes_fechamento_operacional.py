from datetime import datetime
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from empresas.models import Loja, Matriz
from pdv.models import Venda, StatusOperacaoVenda
from configuracoes.models import ConfiguracaoComissaoMatriz, MetaComissaoLoja, FechamentoComissao, ComissaoVendedor
from configuracoes.services_comissoes import fechar_comissoes_competencia

class FechamentoComissaoOperacionalTests(TestCase):
    def setUp(self):
        self.matriz=Matriz.objects.create(nome="Matriz Comissao Operacional")
        self.loja=Loja.objects.create(matriz=self.matriz,nome="Loja Comissao Operacional")
        User=get_user_model()
        self.operador=User.objects.create_user(username="operador_comissao",password="x",matriz=self.matriz)
        self.v1=User.objects.create_user(username="vendedor_a",password="x",first_name="Vendedor",last_name="A",matriz=self.matriz)
        self.v2=User.objects.create_user(username="vendedor_b",password="x",first_name="Vendedor",last_name="B",matriz=self.matriz)
        ConfiguracaoComissaoMatriz.objects.create(matriz=self.matriz,exigir_minimo_individual=True,minimo_vendas_vendedor=Decimal("10000.00"))
        MetaComissaoLoja.objects.create(loja=self.loja,valor_meta=Decimal("50000.00"),percentual_comissao=Decimal("1.5000"))
        MetaComissaoLoja.objects.create(loja=self.loja,valor_meta=Decimal("70000.00"),percentual_comissao=Decimal("3.0000"))
        MetaComissaoLoja.objects.create(loja=self.loja,valor_meta=Decimal("100000.00"),percentual_comissao=Decimal("6.0000"))
    def venda(self,total,vendedor,status=StatusOperacaoVenda.FINALIZADA,cancelada=False):
        dt=timezone.make_aware(datetime(2026,9,15,12,0,0))
        return Venda.objects.create(matriz=self.matriz,loja=self.loja,operador=self.operador,vendedor=vendedor,
            subtotal=Decimal(total),total=Decimal(total),status=status,finalizada_em=dt,
            cancelada_em=(dt if cancelada else None))
    def test_fecha_meta_2_e_persiste_snapshots_sem_recalcular(self):
        self.venda("18000.00",self.v1)
        self.venda("8000.00",self.v2)
        self.venda("56000.00",None)
        self.venda("99999.00",self.v1,cancelada=True)
        f=fechar_comissoes_competencia(loja=self.loja,ano=2026,mes=9)
        self.assertEqual(f.total_vendas_loja,Decimal("82000.00"))
        self.assertEqual(f.valor_meta_atingida,Decimal("70000.00"))
        self.assertEqual(f.percentual_aplicado,Decimal("3.0000"))
        detalhes={d.vendedor_id:d for d in ComissaoVendedor.objects.filter(fechamento=f)}
        self.assertEqual(set(detalhes),{self.v1.id,self.v2.id})
        self.assertEqual(detalhes[self.v1.id].total_vendas_vendedor,Decimal("18000.00"))
        self.assertTrue(detalhes[self.v1.id].elegivel)
        self.assertEqual(detalhes[self.v1.id].valor_comissao,Decimal("540.00"))
        self.assertEqual(detalhes[self.v1.id].vendedor_uuid_original,self.v1.uuid)
        self.assertEqual(detalhes[self.v1.id].vendedor_nome_original,"Vendedor A")
        self.assertEqual(detalhes[self.v2.id].total_vendas_vendedor,Decimal("8000.00"))
        self.assertFalse(detalhes[self.v2.id].elegivel)
        self.assertEqual(detalhes[self.v2.id].valor_comissao,Decimal("0.00"))
        self.assertEqual(ComissaoVendedor.objects.filter(fechamento=f).count(),2)
        MetaComissaoLoja.objects.filter(loja=self.loja,valor_meta=Decimal("70000.00")).update(percentual_comissao=Decimal("9.0000"))
        f2=fechar_comissoes_competencia(loja=self.loja,ano=2026,mes=9)
        self.assertEqual(f2.pk,f.pk)
        f2.refresh_from_db()
        self.assertEqual(f2.percentual_aplicado,Decimal("3.0000"))
        self.assertEqual(FechamentoComissao.objects.filter(loja=self.loja,competencia_ano=2026,competencia_mes=9).count(),1)