from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from auditoria.models import RegistroAuditoria
from empresas.models import Matriz
from produtos.choices import OrigemPreco, StatusProduto
from produtos.models import (
    Categoria,
    Marca,
    Produto,
    UnidadeMedida,
)
from produtos.services import criar_produto, editar_produto


Usuario = get_user_model()


class ProdutoServicesTestCase(TestCase):
    def setUp(self):
        self.matriz = Matriz.objects.create(
            nome='Matriz Principal'
        )

        self.outra_matriz = Matriz.objects.create(
            nome='Outra Matriz'
        )

        self.usuario = Usuario.objects.create_user(
            username='admin_produtos_service',
            password='senha-segura'
        )

        self.categoria = Categoria.objects.create(
            matriz=self.matriz,
            nome='Whey'
        )

        self.marca = Marca.objects.create(
            matriz=self.matriz,
            nome='Pro Corps'
        )

        self.unidade = UnidadeMedida.objects.create(
            matriz=self.matriz,
            sigla='UN',
            descricao='Unidade'
        )

    def dados_produto(self, **alteracoes):
        dados = {
            'categoria': self.categoria,
            'marca': self.marca,
            'unidade_medida': self.unidade,
            'codigo_interno': ' prod-001 ',
            'sku': ' sku-001 ',
            'gtin': '7891234567890',
            'ncm': '2106.90.30',
            'nome': ' Whey Special Flavor ',
            'descricao': ' Produto de teste ',
            'custo_base': Decimal('50.00'),
            'preco_venda': Decimal('100.00'),
            'origem_preco': OrigemPreco.MANUAL,
            'peso_liquido_gramas': 840,
            'peso_bruto_gramas': 950,
            'altura_cm': Decimal('25.00'),
            'largura_cm': Decimal('15.00'),
            'comprimento_cm': Decimal('15.00'),
            'controla_estoque': True,
            'estoque_minimo': Decimal('5.000'),
            'status': StatusProduto.ATIVO,
        }

        dados.update(alteracoes)

        return dados

    def test_cria_produto_normalizando_dados(self):
        produto = criar_produto(
            matriz=self.matriz,
            dados=self.dados_produto(),
            usuario_executor=self.usuario,
        )

        self.assertEqual(
            produto.codigo_interno,
            'PROD-001'
        )
        self.assertEqual(
            produto.sku,
            'SKU-001'
        )
        self.assertEqual(
            produto.ncm,
            '21069030'
        )
        self.assertEqual(
            produto.nome,
            'Whey Special Flavor'
        )
        self.assertEqual(
            produto.descricao,
            'Produto de teste'
        )

    def test_criacao_registra_auditoria(self):
        produto = criar_produto(
            matriz=self.matriz,
            dados=self.dados_produto(),
            usuario_executor=self.usuario,
        )

        registro = RegistroAuditoria.objects.get(
            recurso='produtos.produto',
            recurso_id=str(produto.id),
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
            criar_produto(
                matriz=self.matriz,
                dados=self.dados_produto(nome=' '),
                usuario_executor=self.usuario,
            )

        self.assertIn(
            'nome',
            contexto.exception.message_dict
        )

    def test_impede_codigo_interno_vazio(self):
        with self.assertRaises(ValidationError) as contexto:
            criar_produto(
                matriz=self.matriz,
                dados=self.dados_produto(
                    codigo_interno=' '
                ),
                usuario_executor=self.usuario,
            )

        self.assertIn(
            'codigo_interno',
            contexto.exception.message_dict
        )

    def test_impede_codigo_interno_duplicado(self):
        criar_produto(
            matriz=self.matriz,
            dados=self.dados_produto(),
            usuario_executor=self.usuario,
        )

        with self.assertRaises(ValidationError):
            criar_produto(
                matriz=self.matriz,
                dados=self.dados_produto(
                    sku='SKU-002',
                    gtin='7891234567891',
                ),
                usuario_executor=self.usuario,
            )

    def test_impede_sku_duplicado(self):
        criar_produto(
            matriz=self.matriz,
            dados=self.dados_produto(),
            usuario_executor=self.usuario,
        )

        with self.assertRaises(ValidationError):
            criar_produto(
                matriz=self.matriz,
                dados=self.dados_produto(
                    codigo_interno='PROD-002',
                    gtin='7891234567891',
                ),
                usuario_executor=self.usuario,
            )

    def test_impede_gtin_duplicado(self):
        criar_produto(
            matriz=self.matriz,
            dados=self.dados_produto(),
            usuario_executor=self.usuario,
        )

        with self.assertRaises(ValidationError):
            criar_produto(
                matriz=self.matriz,
                dados=self.dados_produto(
                    codigo_interno='PROD-002',
                    sku='SKU-002',
                ),
                usuario_executor=self.usuario,
            )

    def test_impede_gtin_com_tamanho_invalido(self):
        with self.assertRaises(ValidationError) as contexto:
            criar_produto(
                matriz=self.matriz,
                dados=self.dados_produto(
                    gtin='12345'
                ),
                usuario_executor=self.usuario,
            )

        self.assertIn(
            'gtin',
            contexto.exception.message_dict
        )

    def test_impede_ncm_com_tamanho_invalido(self):
        with self.assertRaises(ValidationError) as contexto:
            criar_produto(
                matriz=self.matriz,
                dados=self.dados_produto(
                    ncm='1234'
                ),
                usuario_executor=self.usuario,
            )

        self.assertIn(
            'ncm',
            contexto.exception.message_dict
        )

    def test_impede_categoria_de_outra_matriz(self):
        categoria = Categoria.objects.create(
            matriz=self.outra_matriz,
            nome='Creatina'
        )

        with self.assertRaises(ValidationError) as contexto:
            criar_produto(
                matriz=self.matriz,
                dados=self.dados_produto(
                    categoria=categoria
                ),
                usuario_executor=self.usuario,
            )

        self.assertIn(
            'categoria',
            contexto.exception.message_dict
        )

    def test_impede_marca_inativa(self):
        self.marca.ativa = False
        self.marca.save(update_fields=['ativa'])

        with self.assertRaises(ValidationError) as contexto:
            criar_produto(
                matriz=self.matriz,
                dados=self.dados_produto(),
                usuario_executor=self.usuario,
            )

        self.assertIn(
            'marca',
            contexto.exception.message_dict
        )

    def test_impede_unidade_inativa(self):
        self.unidade.ativa = False
        self.unidade.save(update_fields=['ativa'])

        with self.assertRaises(ValidationError) as contexto:
            criar_produto(
                matriz=self.matriz,
                dados=self.dados_produto(),
                usuario_executor=self.usuario,
            )

        self.assertIn(
            'unidade_medida',
            contexto.exception.message_dict
        )

    def test_impede_preco_negativo(self):
        with self.assertRaises(ValidationError) as contexto:
            criar_produto(
                matriz=self.matriz,
                dados=self.dados_produto(
                    preco_venda=Decimal('-1.00')
                ),
                usuario_executor=self.usuario,
            )

        self.assertIn(
            'preco_venda',
            contexto.exception.message_dict
        )

    def test_impede_peso_bruto_menor_que_liquido(self):
        with self.assertRaises(ValidationError) as contexto:
            criar_produto(
                matriz=self.matriz,
                dados=self.dados_produto(
                    peso_liquido_gramas=900,
                    peso_bruto_gramas=850,
                ),
                usuario_executor=self.usuario,
            )

        self.assertIn(
            'peso_bruto_gramas',
            contexto.exception.message_dict
        )

    def test_edita_produto(self):
        produto = criar_produto(
            matriz=self.matriz,
            dados=self.dados_produto(),
            usuario_executor=self.usuario,
        )

        produto = editar_produto(
            produto=produto,
            dados={
                'nome': ' Whey Editado ',
                'preco_venda': Decimal('109.90'),
                'status': StatusProduto.INATIVO,
            },
            usuario_executor=self.usuario,
        )

        self.assertEqual(
            produto.nome,
            'Whey Editado'
        )
        self.assertEqual(
            produto.preco_venda,
            Decimal('109.90')
        )
        self.assertEqual(
            produto.status,
            StatusProduto.INATIVO
        )

    def test_edicao_registra_auditoria(self):
        produto = criar_produto(
            matriz=self.matriz,
            dados=self.dados_produto(),
            usuario_executor=self.usuario,
        )

        editar_produto(
            produto=produto,
            dados={
                'nome': 'Produto atualizado'
            },
            usuario_executor=self.usuario,
        )

        registro = RegistroAuditoria.objects.get(
            recurso='produtos.produto',
            recurso_id=str(produto.id),
            acao=RegistroAuditoria.ACAO_EDITAR,
        )

        self.assertEqual(
            registro.usuario,
            self.usuario
        )

    def test_edicao_preserva_campos_nao_informados(self):
        produto = criar_produto(
            matriz=self.matriz,
            dados=self.dados_produto(),
            usuario_executor=self.usuario,
        )

        produto = editar_produto(
            produto=produto,
            dados={
                'descricao': 'Descrição alterada'
            },
            usuario_executor=self.usuario,
        )

        self.assertEqual(
            produto.codigo_interno,
            'PROD-001'
        )
        self.assertEqual(
            produto.preco_venda,
            Decimal('100.00')
        )
        self.assertEqual(
            produto.descricao,
            'Descrição alterada'
        )
