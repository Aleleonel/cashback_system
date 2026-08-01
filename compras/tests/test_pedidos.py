from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from auditoria.models import RegistroAuditoria
from empresas.models import Matriz

from compras.choices import (
    StatusFornecedor,
    StatusPedidoCompra,
)
from compras.models import (
    Fornecedor,
    PedidoCompra,
)
from compras.services import (
    cancelar_pedido_compra,
    criar_pedido_compra,
    editar_pedido_compra,
    enviar_pedido_compra,
)


Usuario = get_user_model()


class PedidoCompraServicesTestCase(TestCase):
    def setUp(self):
        self.matriz = Matriz.objects.create(
            nome='Matriz Pedidos'
        )

        self.outra_matriz = Matriz.objects.create(
            nome='Outra Matriz Pedidos'
        )

        self.usuario = Usuario.objects.create_user(
            username='admin_pedidos',
            password='senha-segura',
            matriz=self.matriz,
        )

        self.fornecedor = Fornecedor.objects.create(
            matriz=self.matriz,
            razao_social='Fornecedor Pedidos LTDA',
            cnpj='11222333000181',
            status=StatusFornecedor.ATIVO,
        )

        self.hoje = timezone.localdate()

    def criar_pedido(self, **alteracoes):
        dados = {
            'matriz': self.matriz,
            'fornecedor': self.fornecedor,
            'data_emissao': self.hoje,
            'previsao_entrega': (
                self.hoje + timedelta(days=7)
            ),
            'condicao_pagamento': '30 dias',
            'frete': Decimal('10.00'),
            'desconto': Decimal('2.00'),
            'observacoes': 'Pedido de teste',
            'usuario': self.usuario,
        }

        dados.update(alteracoes)

        return criar_pedido_compra(**dados)

    def test_cria_pedido_com_numero_sequencial(self):
        primeiro = self.criar_pedido()
        segundo = self.criar_pedido()

        self.assertEqual(primeiro.numero, 1)
        self.assertEqual(segundo.numero, 2)
        self.assertEqual(
            primeiro.status,
            StatusPedidoCompra.RASCUNHO,
        )

    def test_numero_e_independente_por_matriz(self):
        self.criar_pedido()

        usuario_outra = Usuario.objects.create_user(
            username='admin_outra_matriz',
            password='senha-segura',
            matriz=self.outra_matriz,
        )

        fornecedor_outra = Fornecedor.objects.create(
            matriz=self.outra_matriz,
            razao_social='Fornecedor Outra Matriz LTDA',
            cnpj='11444777000161',
        )

        pedido_outra = criar_pedido_compra(
            matriz=self.outra_matriz,
            fornecedor=fornecedor_outra,
            data_emissao=self.hoje,
            usuario=usuario_outra,
        )

        self.assertEqual(
            pedido_outra.numero,
            1,
        )

    def test_rejeita_fornecedor_de_outra_matriz(self):
        fornecedor_outra = Fornecedor.objects.create(
            matriz=self.outra_matriz,
            razao_social='Fornecedor Invalido LTDA',
            cnpj='27865757000102',
        )

        with self.assertRaises(ValidationError):
            self.criar_pedido(
                fornecedor=fornecedor_outra
            )

    def test_rejeita_previsao_anterior_a_emissao(self):
        with self.assertRaises(ValidationError):
            self.criar_pedido(
                previsao_entrega=(
                    self.hoje - timedelta(days=1)
                )
            )

    def test_edita_pedido_em_rascunho(self):
        pedido = self.criar_pedido()

        pedido = editar_pedido_compra(
            pedido=pedido,
            fornecedor=self.fornecedor,
            data_emissao=self.hoje,
            previsao_entrega=(
                self.hoje + timedelta(days=10)
            ),
            condicao_pagamento='45 dias',
            frete=Decimal('20.00'),
            desconto=Decimal('5.00'),
            observacoes='Alterado',
            usuario=self.usuario,
        )

        self.assertEqual(
            pedido.condicao_pagamento,
            '45 dias',
        )
        self.assertEqual(
            pedido.frete,
            Decimal('20.00'),
        )

    def test_nao_envia_pedido_sem_itens(self):
        pedido = self.criar_pedido()

        with self.assertRaises(ValidationError):
            enviar_pedido_compra(
                pedido=pedido,
                usuario=self.usuario,
            )

    def test_cancela_pedido(self):
        pedido = self.criar_pedido()

        pedido = cancelar_pedido_compra(
            pedido=pedido,
            usuario=self.usuario,
        )

        self.assertEqual(
            pedido.status,
            StatusPedidoCompra.CANCELADO,
        )
        self.assertIsNotNone(
            pedido.cancelado_em,
        )

    def test_criacao_registra_auditoria(self):
        pedido = self.criar_pedido()

        auditoria = RegistroAuditoria.objects.get(
            recurso='compras.pedido_compra',
            recurso_id=str(pedido.uuid),
            acao=RegistroAuditoria.ACAO_CRIAR,
        )

        self.assertEqual(
            auditoria.matriz,
            self.matriz,
        )

    def test_falha_na_auditoria_desfaz_criacao(self):
        with patch(
            'compras.services.pedidos.registrar_auditoria',
            side_effect=RuntimeError(
                'Falha simulada de auditoria'
            ),
        ):
            with self.assertRaises(RuntimeError):
                self.criar_pedido()

        self.assertFalse(
            PedidoCompra.objects.exists()
        )