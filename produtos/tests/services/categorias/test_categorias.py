from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from auditoria.models import RegistroAuditoria
from empresas.models import Matriz
from produtos.models import Categoria
from produtos.services import criar_categoria, editar_categoria


Usuario = get_user_model()


class CategoriaServicesTestCase(TestCase):
    def setUp(self):
        self.matriz = Matriz.objects.create(
            nome='Matriz Principal'
        )

        self.usuario = Usuario.objects.create_user(
            username='admin_produtos',
            password='senha-segura'
        )

    def test_cria_categoria(self):
        categoria = criar_categoria(
            matriz=self.matriz,
            dados={
                'nome': ' Whey Protein ',
                'descricao': ' Categoria de whey ',
                'ativa': True,
            },
            usuario_executor=self.usuario,
        )

        self.assertEqual(
            categoria.nome,
            'Whey Protein'
        )
        self.assertEqual(
            categoria.descricao,
            'Categoria de whey'
        )
        self.assertTrue(
            categoria.ativa
        )

    def test_criacao_registra_auditoria(self):
        categoria = criar_categoria(
            matriz=self.matriz,
            dados={
                'nome': 'Creatina',
                'descricao': '',
                'ativa': True,
            },
            usuario_executor=self.usuario,
        )

        registro = RegistroAuditoria.objects.get(
            recurso='produtos.categoria',
            recurso_id=str(categoria.id),
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
            criar_categoria(
                matriz=self.matriz,
                dados={
                    'nome': ' ',
                    'descricao': '',
                    'ativa': True,
                },
                usuario_executor=self.usuario,
            )

        self.assertIn(
            'nome',
            contexto.exception.message_dict
        )

    def test_impede_nome_duplicado_sem_diferenciar_maiusculas(self):
        Categoria.objects.create(
            matriz=self.matriz,
            nome='Whey'
        )

        with self.assertRaises(ValidationError):
            criar_categoria(
                matriz=self.matriz,
                dados={
                    'nome': 'whey',
                    'descricao': '',
                    'ativa': True,
                },
                usuario_executor=self.usuario,
            )

    def test_permite_nome_igual_em_matriz_diferente(self):
        outra_matriz = Matriz.objects.create(
            nome='Outra Matriz'
        )

        primeira = criar_categoria(
            matriz=self.matriz,
            dados={
                'nome': 'Whey',
                'descricao': '',
                'ativa': True,
            },
            usuario_executor=self.usuario,
        )

        segunda = criar_categoria(
            matriz=outra_matriz,
            dados={
                'nome': 'Whey',
                'descricao': '',
                'ativa': True,
            },
            usuario_executor=self.usuario,
        )

        self.assertNotEqual(
            primeira.matriz_id,
            segunda.matriz_id
        )

    def test_edita_categoria(self):
        categoria = Categoria.objects.create(
            matriz=self.matriz,
            nome='Whey'
        )

        categoria = editar_categoria(
            categoria=categoria,
            dados={
                'nome': ' Whey Protein ',
                'descricao': ' Nova descrição ',
                'ativa': False,
            },
            usuario_executor=self.usuario,
        )

        self.assertEqual(
            categoria.nome,
            'Whey Protein'
        )
        self.assertEqual(
            categoria.descricao,
            'Nova descrição'
        )
        self.assertFalse(
            categoria.ativa
        )

    def test_edicao_registra_auditoria(self):
        categoria = Categoria.objects.create(
            matriz=self.matriz,
            nome='Whey'
        )

        editar_categoria(
            categoria=categoria,
            dados={
                'nome': 'Whey Protein',
                'descricao': '',
                'ativa': True,
            },
            usuario_executor=self.usuario,
        )

        registro = RegistroAuditoria.objects.get(
            recurso='produtos.categoria',
            recurso_id=str(categoria.id),
            acao=RegistroAuditoria.ACAO_EDITAR,
        )

        self.assertEqual(
            registro.usuario,
            self.usuario
        )

    def test_edicao_nao_considera_o_proprio_registro_duplicado(self):
        categoria = Categoria.objects.create(
            matriz=self.matriz,
            nome='Whey'
        )

        categoria = editar_categoria(
            categoria=categoria,
            dados={
                'nome': 'Whey',
                'descricao': 'Atualizada',
                'ativa': True,
            },
            usuario_executor=self.usuario,
        )

        self.assertEqual(
            categoria.descricao,
            'Atualizada'
        )

    def test_edicao_impede_nome_usado_por_outra_categoria(self):
        primeira = Categoria.objects.create(
            matriz=self.matriz,
            nome='Whey'
        )

        Categoria.objects.create(
            matriz=self.matriz,
            nome='Creatina'
        )

        with self.assertRaises(ValidationError):
            editar_categoria(
                categoria=primeira,
                dados={
                    'nome': 'creatina',
                    'descricao': '',
                    'ativa': True,
                },
                usuario_executor=self.usuario,
            )
