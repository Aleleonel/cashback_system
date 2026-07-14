from decimal import Decimal
from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.test import TestCase

from empresas.models import Matriz
from produtos.importacao import (
    executar_importacao_produtos,
    validar_linhas_para_confirmacao,
)
from produtos.models import (
    Categoria,
    Marca,
    Produto,
    UnidadeMedida,
)


class ExecutorImportacaoProdutosTestCase(TestCase):
    def setUp(self):
        self.matriz = Matriz.objects.create(
            nome='Matriz Executor'
        )

        self.categoria = Categoria.objects.create(
            matriz=self.matriz,
            nome='Suplementos',
            ativa=True,
        )

        self.marca = Marca.objects.create(
            matriz=self.matriz,
            nome='Marca Executor',
            ativa=True,
        )

        self.unidade = UnidadeMedida.objects.create(
            matriz=self.matriz,
            sigla='UN',
            descricao='Unidade',
            ativa=True,
        )

    def linha_valida(
        self,
        *,
        codigo='PROD-001',
        nome='Produto Importado',
        produto_id=None,
        acao='novo',
        preco='99.90',
    ):
        return {
            'linha': 2,
            'produto_id': produto_id,
            'codigo_interno': codigo,
            'nome': nome,
            'sku': '',
            'gtin': '',
            'ncm': '21069030',
            'descricao': 'Produto de teste.',
            'categoria_id': self.categoria.id,
            'marca_id': self.marca.id,
            'unidade_medida_id': self.unidade.id,
            'custo_base': '50.00',
            'preco_venda': preco,
            'origem_preco': 'manual',
            'peso_liquido_gramas': 900,
            'peso_bruto_gramas': 1000,
            'altura_cm': '25.00',
            'largura_cm': '15.00',
            'comprimento_cm': '15.00',
            'controla_estoque': True,
            'estoque_minimo': '5.000',
            'produto_status': 'ativo',
            'acao_prevista': acao,
            'status': acao,
            'valido': True,
            'erros': [],
        }

    @patch(
        'produtos.importacao.executor.'
        'registrar_auditoria'
    )
    def test_cria_produto_na_confirmacao(
        self,
        mock_auditoria,
    ):
        resultado = executar_importacao_produtos(
            matriz=self.matriz,
            loja=None,
            linhas=[
                self.linha_valida()
            ],
            usuario_executor=None,
        )

        produto = Produto.objects.get(
            matriz=self.matriz,
            codigo_interno='PROD-001',
        )

        self.assertEqual(
            produto.nome,
            'Produto Importado'
        )
        self.assertEqual(
            produto.preco_venda,
            Decimal('99.90')
        )
        self.assertEqual(
            resultado['criados'],
            1
        )
        self.assertEqual(
            resultado['atualizados'],
            0
        )

    @patch(
        'produtos.importacao.executor.'
        'registrar_auditoria'
    )
    def test_atualiza_produto_existente(
        self,
        mock_auditoria,
    ):
        produto = Produto.objects.create(
            matriz=self.matriz,
            categoria=self.categoria,
            marca=self.marca,
            unidade_medida=self.unidade,
            codigo_interno='PROD-001',
            nome='Nome antigo',
            custo_base='20.00',
            preco_venda='40.00',
        )

        resultado = executar_importacao_produtos(
            matriz=self.matriz,
            loja=None,
            linhas=[
                self.linha_valida(
                    produto_id=produto.id,
                    acao='atualizar',
                    nome='Nome atualizado',
                    preco='119.90',
                )
            ],
            usuario_executor=None,
        )

        produto.refresh_from_db()

        self.assertEqual(
            produto.nome,
            'Nome atualizado'
        )
        self.assertEqual(
            produto.preco_venda,
            Decimal('119.90')
        )
        self.assertEqual(
            resultado['criados'],
            0
        )
        self.assertEqual(
            resultado['atualizados'],
            1
        )

    def test_bloqueia_linhas_invalidas(self):
        linha = self.linha_valida()
        linha['valido'] = False
        linha['status'] = 'invalido'
        linha['erros'] = [
            'Produto inválido.'
        ]

        with self.assertRaises(
            ValidationError
        ):
            validar_linhas_para_confirmacao([
                linha
            ])

    @patch(
        'produtos.importacao.executor.'
        'registrar_auditoria'
    )
    def test_rollback_quando_segunda_linha_falha(
        self,
        mock_auditoria,
    ):
        linha_valida = self.linha_valida(
            codigo='PROD-001'
        )

        linha_com_erro = self.linha_valida(
            codigo='PROD-002',
            nome='Produto inválido',
        )

        linha_com_erro[
            'unidade_medida_id'
        ] = 999999

        with self.assertRaises(
            ValidationError
        ):
            executar_importacao_produtos(
                matriz=self.matriz,
                loja=None,
                linhas=[
                    linha_valida,
                    linha_com_erro,
                ],
                usuario_executor=None,
            )

        self.assertFalse(
            Produto.objects.filter(
                matriz=self.matriz,
                codigo_interno='PROD-001',
            ).exists()
        )

    @patch(
        'produtos.importacao.executor.'
        'registrar_auditoria'
    )
    def test_registra_auditoria_resumida(
        self,
        mock_auditoria,
    ):
        executar_importacao_produtos(
            matriz=self.matriz,
            loja=None,
            linhas=[
                self.linha_valida()
            ],
            usuario_executor=None,
        )

        mock_auditoria.assert_called_once()

        chamada = mock_auditoria.call_args.kwargs

        self.assertEqual(
            chamada['recurso'],
            'produtos.importacao'
        )
        self.assertIn(
            'Criados: 1',
            chamada['descricao']
        )
