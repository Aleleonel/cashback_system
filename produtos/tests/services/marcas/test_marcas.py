from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from auditoria.models import RegistroAuditoria
from empresas.models import Matriz
from produtos.models import Marca
from produtos.services import criar_marca, editar_marca


Usuario = get_user_model()


class MarcaServicesTestCase(TestCase):
    def setUp(self):
        self.matriz = Matriz.objects.create(
            nome='Matriz Principal'
        )

        self.usuario = Usuario.objects.create_user(
            username='admin_marcas',
            password='senha-segura'
        )

    def test_cria_marca(self):
        marca = criar_marca(
            matriz=self.matriz,
            dados={
                'nome': ' Pro Corps ',
                'fabricante': ' Pro Corps Suplementos ',
                'ativa': True,
            },
            usuario_executor=self.usuario,
        )

        self.assertEqual(
            marca.nome,
            'Pro Corps'
        )
        self.assertEqual(
            marca.fabricante,
            'Pro Corps Suplementos'
        )
        self.assertTrue(marca.ativa)

    def test_criacao_registra_auditoria(self):
        marca = criar_marca(
            matriz=self.matriz,
            dados={
                'nome': 'Pro Corps',
                'fabricante': '',
                'ativa': True,
            },
            usuario_executor=self.usuario,
        )

        registro = RegistroAuditoria.objects.get(
            recurso='produtos.marca',
            recurso_id=str(marca.id),
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

    def test_impede_nome_vazio(self):
        with self.assertRaises(ValidationError) as contexto:
            criar_marca(
                matriz=self.matriz,
                dados={
                    'nome': ' ',
                    'fabricante': '',
                    'ativa': True,
                },
                usuario_executor=self.usuario,
            )

        self.assertIn(
            'nome',
            contexto.exception.message_dict
        )

    def test_impede_nome_duplicado_sem_diferenciar_maiusculas(self):
        Marca.objects.create(
            matriz=self.matriz,
            nome='Pro Corps'
        )

        with self.assertRaises(ValidationError):
            criar_marca(
                matriz=self.matriz,
                dados={
                    'nome': 'pro corps',
                    'fabricante': '',
                    'ativa': True,
                },
                usuario_executor=self.usuario,
            )

    def test_permite_nome_igual_em_matriz_diferente(self):
        outra_matriz = Matriz.objects.create(
            nome='Outra Matriz'
        )

        primeira = criar_marca(
            matriz=self.matriz,
            dados={
                'nome': 'Pro Corps',
                'fabricante': '',
                'ativa': True,
            },
            usuario_executor=self.usuario,
        )

        segunda = criar_marca(
            matriz=outra_matriz,
            dados={
                'nome': 'Pro Corps',
                'fabricante': '',
                'ativa': True,
            },
            usuario_executor=self.usuario,
        )

        self.assertNotEqual(
            primeira.matriz_id,
            segunda.matriz_id
        )

    def test_edita_marca(self):
        marca = Marca.objects.create(
            matriz=self.matriz,
            nome='Procorps'
        )

        marca = editar_marca(
            marca=marca,
            dados={
                'nome': ' Pro Corps ',
                'fabricante': ' Novo fabricante ',
                'ativa': False,
            },
            usuario_executor=self.usuario,
        )

        self.assertEqual(
            marca.nome,
            'Pro Corps'
        )
        self.assertEqual(
            marca.fabricante,
            'Novo fabricante'
        )
        self.assertFalse(marca.ativa)

    def test_edicao_registra_auditoria(self):
        marca = Marca.objects.create(
            matriz=self.matriz,
            nome='Pro Corps'
        )

        editar_marca(
            marca=marca,
            dados={
                'nome': 'Pro Corps',
                'fabricante': 'Fabricante',
                'ativa': True,
            },
            usuario_executor=self.usuario,
        )

        registro = RegistroAuditoria.objects.get(
            recurso='produtos.marca',
            recurso_id=str(marca.id),
            acao=RegistroAuditoria.ACAO_EDITAR,
        )

        self.assertEqual(
            registro.usuario,
            self.usuario
        )

    def test_edicao_nao_considera_proprio_registro_duplicado(self):
        marca = Marca.objects.create(
            matriz=self.matriz,
            nome='Pro Corps'
        )

        marca = editar_marca(
            marca=marca,
            dados={
                'nome': 'Pro Corps',
                'fabricante': 'Atualizado',
                'ativa': True,
            },
            usuario_executor=self.usuario,
        )

        self.assertEqual(
            marca.fabricante,
            'Atualizado'
        )

    def test_edicao_impede_nome_usado_por_outra_marca(self):
        primeira = Marca.objects.create(
            matriz=self.matriz,
            nome='Pro Corps'
        )

        Marca.objects.create(
            matriz=self.matriz,
            nome='Outra Marca'
        )

        with self.assertRaises(ValidationError):
            editar_marca(
                marca=primeira,
                dados={
                    'nome': 'outra marca',
                    'fabricante': '',
                    'ativa': True,
                },
                usuario_executor=self.usuario,
            )
