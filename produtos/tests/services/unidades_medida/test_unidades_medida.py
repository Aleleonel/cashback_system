from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from auditoria.models import RegistroAuditoria
from empresas.models import Matriz
from produtos.models import UnidadeMedida
from produtos.services import (
    criar_unidade_medida,
    editar_unidade_medida,
)


Usuario = get_user_model()


class UnidadeMedidaServicesTestCase(TestCase):
    def setUp(self):
        self.matriz = Matriz.objects.create(
            nome='Matriz Principal'
        )

        self.usuario = Usuario.objects.create_user(
            username='admin_unidades',
            password='senha-segura'
        )

    def test_cria_unidade_medida_normalizando_campos(self):
        unidade = criar_unidade_medida(
            matriz=self.matriz,
            dados={
                'sigla': ' un ',
                'descricao': ' Unidade ',
                'ativa': True,
            },
            usuario_executor=self.usuario,
        )

        self.assertEqual(
            unidade.sigla,
            'UN'
        )
        self.assertEqual(
            unidade.descricao,
            'Unidade'
        )
        self.assertTrue(unidade.ativa)

    def test_criacao_registra_auditoria(self):
        unidade = criar_unidade_medida(
            matriz=self.matriz,
            dados={
                'sigla': 'UN',
                'descricao': 'Unidade',
                'ativa': True,
            },
            usuario_executor=self.usuario,
        )

        registro = RegistroAuditoria.objects.get(
            recurso='produtos.unidade_medida',
            recurso_id=str(unidade.id),
            acao=RegistroAuditoria.ACAO_CRIAR,
        )

        self.assertEqual(
            registro.usuario,
            self.usuario
        )
        self.assertEqual(
            registro.matriz,
            self.matriz
        )

    def test_impede_sigla_vazia(self):
        with self.assertRaises(ValidationError) as contexto:
            criar_unidade_medida(
                matriz=self.matriz,
                dados={
                    'sigla': ' ',
                    'descricao': 'Unidade',
                    'ativa': True,
                },
                usuario_executor=self.usuario,
            )

        self.assertIn(
            'sigla',
            contexto.exception.message_dict
        )

    def test_impede_descricao_vazia(self):
        with self.assertRaises(ValidationError) as contexto:
            criar_unidade_medida(
                matriz=self.matriz,
                dados={
                    'sigla': 'UN',
                    'descricao': ' ',
                    'ativa': True,
                },
                usuario_executor=self.usuario,
            )

        self.assertIn(
            'descricao',
            contexto.exception.message_dict
        )

    def test_impede_sigla_duplicada_na_mesma_matriz(self):
        UnidadeMedida.objects.create(
            matriz=self.matriz,
            sigla='UN',
            descricao='Unidade'
        )

        with self.assertRaises(ValidationError):
            criar_unidade_medida(
                matriz=self.matriz,
                dados={
                    'sigla': 'un',
                    'descricao': 'Outra unidade',
                    'ativa': True,
                },
                usuario_executor=self.usuario,
            )

    def test_permite_sigla_igual_em_matriz_diferente(self):
        outra_matriz = Matriz.objects.create(
            nome='Outra Matriz'
        )

        primeira = criar_unidade_medida(
            matriz=self.matriz,
            dados={
                'sigla': 'UN',
                'descricao': 'Unidade',
                'ativa': True,
            },
            usuario_executor=self.usuario,
        )

        segunda = criar_unidade_medida(
            matriz=outra_matriz,
            dados={
                'sigla': 'UN',
                'descricao': 'Unidade',
                'ativa': True,
            },
            usuario_executor=self.usuario,
        )

        self.assertNotEqual(
            primeira.matriz_id,
            segunda.matriz_id
        )

    def test_edita_unidade_medida(self):
        unidade = UnidadeMedida.objects.create(
            matriz=self.matriz,
            sigla='PC',
            descricao='Peça'
        )

        unidade = editar_unidade_medida(
            unidade=unidade,
            dados={
                'sigla': ' cx ',
                'descricao': ' Caixa ',
                'ativa': False,
            },
            usuario_executor=self.usuario,
        )

        self.assertEqual(
            unidade.sigla,
            'CX'
        )
        self.assertEqual(
            unidade.descricao,
            'Caixa'
        )
        self.assertFalse(unidade.ativa)

    def test_edicao_registra_auditoria(self):
        unidade = UnidadeMedida.objects.create(
            matriz=self.matriz,
            sigla='UN',
            descricao='Unidade'
        )

        editar_unidade_medida(
            unidade=unidade,
            dados={
                'sigla': 'UN',
                'descricao': 'Unidade atualizada',
                'ativa': True,
            },
            usuario_executor=self.usuario,
        )

        registro = RegistroAuditoria.objects.get(
            recurso='produtos.unidade_medida',
            recurso_id=str(unidade.id),
            acao=RegistroAuditoria.ACAO_EDITAR,
        )

        self.assertEqual(
            registro.usuario,
            self.usuario
        )

    def test_edicao_nao_considera_proprio_registro_duplicado(self):
        unidade = UnidadeMedida.objects.create(
            matriz=self.matriz,
            sigla='UN',
            descricao='Unidade'
        )

        unidade = editar_unidade_medida(
            unidade=unidade,
            dados={
                'sigla': 'UN',
                'descricao': 'Unidade atualizada',
                'ativa': True,
            },
            usuario_executor=self.usuario,
        )

        self.assertEqual(
            unidade.descricao,
            'Unidade atualizada'
        )

    def test_edicao_impede_sigla_usada_por_outra_unidade(self):
        primeira = UnidadeMedida.objects.create(
            matriz=self.matriz,
            sigla='UN',
            descricao='Unidade'
        )

        UnidadeMedida.objects.create(
            matriz=self.matriz,
            sigla='CX',
            descricao='Caixa'
        )

        with self.assertRaises(ValidationError):
            editar_unidade_medida(
                unidade=primeira,
                dados={
                    'sigla': 'cx',
                    'descricao': 'Nova descrição',
                    'ativa': True,
                },
                usuario_executor=self.usuario,
            )
