from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase
from empresas.models import Matriz, Loja
from clientes.models import Cliente
from pdv.models import Venda

class Cliente360NucleoTests(TestCase):
    def setUp(self):
        self.matriz = Matriz.objects.create(nome="Matriz 360")
        self.loja_origem = Loja.objects.create(matriz=self.matriz, nome="Loja Origem")
        self.loja_2 = Loja.objects.create(matriz=self.matriz, nome="Loja 2")
        User = get_user_model()
        self.operador = User.objects.create_user(
            username="operador_cliente_360",
            password="teste123",
            perfil=User.PERFIL_OPERADOR,
            matriz=self.matriz,
        )
        self.cliente = Cliente.objects.create(
            matriz=self.matriz, loja_cadastro=self.loja_origem,
            nome="Cliente Teste 360", cpf="52998224725", tipo_pessoa="PF"
        )

    def venda(self, loja, total, status="finalizada"):
        return Venda.objects.create(
            matriz=self.matriz, loja=loja, cliente=self.cliente, operador=self.operador,
            total=Decimal(total), subtotal=Decimal(total), status=status
        )

    def test_agrega_vendas_finalizadas_de_lojas_distintas_da_mesma_matriz(self):
        from clientes.selectors import obter_cliente_360
        self.venda(self.loja_origem, "100.00")
        self.venda(self.loja_2, "200.00")
        r = obter_cliente_360(self.cliente)
        self.assertEqual(r["quantidade_compras"], 2)
        self.assertEqual(r["total_gasto"], Decimal("300.00"))
        self.assertEqual(r["ticket_medio"], Decimal("150.00"))
        self.assertEqual(len(r["historico_vendas"]), 2)
        self.assertEqual({v.loja_id for v in r["historico_vendas"]}, {self.loja_origem.id, self.loja_2.id})

    def test_exclui_venda_cancelada_das_metricas_e_historico(self):
        from clientes.selectors import obter_cliente_360
        self.venda(self.loja_origem, "100.00")
        self.venda(self.loja_2, "999.00", status="cancelada")
        r = obter_cliente_360(self.cliente)
        self.assertEqual(r["quantidade_compras"], 1)
        self.assertEqual(r["total_gasto"], Decimal("100.00"))
        self.assertEqual(len(r["historico_vendas"]), 1)

    def test_cliente_sem_compras_retorna_zeros_e_ultima_nula(self):
        from clientes.selectors import obter_cliente_360
        r = obter_cliente_360(self.cliente)
        self.assertEqual(r["quantidade_compras"], 0)
        self.assertEqual(r["total_gasto"], Decimal("0"))
        self.assertEqual(r["ticket_medio"], Decimal("0"))
        self.assertIsNone(r["ultima_compra"])
        self.assertEqual(list(r["historico_vendas"]), [])


    def test_isola_venda_inconsistente_de_outra_matriz(self):
        from django.contrib.auth import get_user_model
        from clientes.selectors import obter_cliente_360

        outra_matriz = Matriz.objects.create(nome="Outra Matriz Vendas 360")
        outra_loja = Loja.objects.create(matriz=outra_matriz, nome="Outra Loja Vendas 360")

        User = get_user_model()
        outro_operador = User.objects.create_user(
            username="operador_outra_matriz_360",
            password="teste123",
            perfil=User.PERFIL_OPERADOR,
            matriz=outra_matriz,
        )

        Venda.objects.create(
            matriz=outra_matriz,
            loja=outra_loja,
            cliente=self.cliente,
            operador=outro_operador,
            total=Decimal("999.00"),
            subtotal=Decimal("999.00"),
            status="finalizada",
        )

        r = obter_cliente_360(self.cliente)

        self.assertEqual(r["quantidade_compras"], 0)
        self.assertEqual(r["total_gasto"], Decimal("0"))
        self.assertEqual(list(r["historico_vendas"]), [])

    def test_ultima_compra_retorna_finalizada_em_mais_recente(self):
        from datetime import timedelta
        from django.utils import timezone
        from clientes.selectors import obter_cliente_360

        antiga = timezone.now() - timedelta(days=5)
        recente = timezone.now() - timedelta(days=1)

        Venda.objects.create(
            matriz=self.matriz,
            loja=self.loja_origem,
            cliente=self.cliente,
            operador=self.operador,
            total=Decimal("100.00"),
            subtotal=Decimal("100.00"),
            status="finalizada",
            finalizada_em=antiga,
        )
        Venda.objects.create(
            matriz=self.matriz,
            loja=self.loja_2,
            cliente=self.cliente,
            operador=self.operador,
            total=Decimal("200.00"),
            subtotal=Decimal("200.00"),
            status="finalizada",
            finalizada_em=recente,
        )

        r = obter_cliente_360(self.cliente)

        self.assertEqual(r["ultima_compra"], recente)
        self.assertEqual(r["historico_vendas"][0].finalizada_em, recente)
