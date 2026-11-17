"""F33C4F: regressao do ciclo de vida da imagem no servico de produtos."""
import base64
import tempfile
from decimal import Decimal
from pathlib import Path
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from empresas.models import Matriz
from produtos.models import Categoria, Marca, UnidadeMedida
from produtos.services import criar_produto, editar_produto

PNG = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/lXcAAAAASUVORK5CYII=')

class F33C4FCicloVidaImagemTests(TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='f33c4f_')
        self.addCleanup(self.tmp.cleanup)
        self.media = override_settings(MEDIA_ROOT=self.tmp.name)
        self.media.enable()
        self.addCleanup(self.media.disable)
        self.matriz = Matriz.objects.create(nome='Matriz F33C4F')
        self.usuario = get_user_model().objects.create_user(username='f33c4f', password='teste')
        self.categoria = Categoria.objects.create(matriz=self.matriz, nome='Suplementos')
        self.marca = Marca.objects.create(matriz=self.matriz, nome='Marca F33C4F')
        self.unidade = UnidadeMedida.objects.create(matriz=self.matriz, sigla='UN', descricao='Unidade')

    def imagem(self, nome):
        return SimpleUploadedFile(nome, PNG, content_type='image/png')

    def dados(self, **kwargs):
        dados = dict(categoria=self.categoria, marca=self.marca, unidade_medida=self.unidade,
            codigo_interno='F33C4F-01', sku='F33C4F-01', nome='Produto Imagem F33C4F',
            custo_base=Decimal('10.00'), preco_venda=Decimal('20.00'),
            controla_estoque=True, estoque_minimo=Decimal('0.000'))
        dados.update(kwargs)
        return dados

    def criar(self, **kwargs):
        return criar_produto(matriz=self.matriz, dados=self.dados(**kwargs), usuario_executor=self.usuario)

    def test_criacao_grava_imagem_na_matriz_correta(self):
        produto = self.criar(imagem_principal=self.imagem('original.png'))
        self.assertTrue(produto.imagem_principal.name)
        self.assertIn('produtos/matriz_%s/' % self.matriz.pk, produto.imagem_principal.name)
        self.assertTrue(Path(produto.imagem_principal.path).is_file())

    def test_substituicao_nao_deixa_arquivo_orfao(self):
        produto = self.criar(imagem_principal=self.imagem('primeira.png'))
        antigo = Path(produto.imagem_principal.path)
        with self.captureOnCommitCallbacks(execute=True):
            editar_produto(produto=produto, dados={'imagem_principal': self.imagem('segunda.png')}, usuario_executor=self.usuario)
        produto.refresh_from_db()
        self.assertTrue(Path(produto.imagem_principal.path).is_file())
        self.assertNotEqual(antigo, Path(produto.imagem_principal.path))
        self.assertFalse(antigo.exists(), 'Imagem substituida permaneceu no disco')

    def test_remocao_apaga_arquivo_anterior(self):
        produto = self.criar(imagem_principal=self.imagem('remover.png'))
        antigo = Path(produto.imagem_principal.path)
        with self.captureOnCommitCallbacks(execute=True):
            editar_produto(produto=produto, dados={'remover_imagem': True}, usuario_executor=self.usuario)
        produto.refresh_from_db()
        self.assertFalse(produto.imagem_principal)
        self.assertFalse(antigo.exists(), 'Imagem removida permaneceu no disco')
