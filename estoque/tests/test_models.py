import uuid
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError
from django.test import TestCase

from core.choices import StatusOperacional
from empresas.models import Loja, Matriz
from estoque.choices import (
    NaturezaMovimentacao,
    OrigemMovimentacao,
    TipoMovimentacao,
)
from estoque.models import MovimentacaoEstoque, SaldoEstoque
from produtos.models import Produto, UnidadeMedida


class SaldoEstoqueModelTestCase(TestCase):
    def setUp(self):
        self.matriz = Matriz.objects.create(
            nome='Matriz Estoque'
        )

        self.loja = Loja.objects.create(
            matriz=self.matriz,
            nome='Loja Estoque',
            status=StatusOperacional.ATIVA,
        )

        self.unidade = UnidadeMedida.objects.create(
            matriz=self.matriz,
            sigla='UN',
            descricao='Unidade',
        )

        self.produto = Produto.objects.create(
            matriz=self.matriz,
            unidade_medida=self.unidade,
            codigo_interno='EST-001',
            nome='Produto Estoque',
            controla_estoque=True,
        )

    def criar_saldo(self, **dados):
        padrao = {
            'matriz': self.matriz,
            'loja': self.loja,
            'produto': self.produto,
            'quantidade_atual': Decimal('0.000'),
        }

        padrao.update(dados)

        return SaldoEstoque.objects.create(**padrao)

    def test_cria_saldo_zerado_valido(self):
        saldo = self.criar_saldo()

        self.assertEqual(
            saldo.quantidade_atual,
            Decimal('0.000')
        )
        self.assertIsNone(saldo.ultima_movimentacao_em)
        self.assertIsNotNone(saldo.uuid)
        self.assertIsNotNone(saldo.criado_em)
        self.assertIsNotNone(saldo.atualizado_em)

    def test_aceita_quantidade_com_tres_casas_decimais(self):
        saldo = self.criar_saldo(
            quantidade_atual=Decimal('10.125')
        )

        saldo.refresh_from_db()

        self.assertEqual(
            saldo.quantidade_atual,
            Decimal('10.125')
        )

    def test_rejeita_quantidade_negativa_no_model(self):
        saldo = SaldoEstoque(
            matriz=self.matriz,
            loja=self.loja,
            produto=self.produto,
            quantidade_atual=Decimal('-0.001'),
        )

        with self.assertRaises(ValidationError):
            saldo.full_clean()

    def test_rejeita_quantidade_negativa_no_banco(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                SaldoEstoque.objects.bulk_create([
                    SaldoEstoque(
                        matriz=self.matriz,
                        loja=self.loja,
                        produto=self.produto,
                        quantidade_atual=Decimal('-1.000'),
                    )
                ])

    def test_impede_saldo_duplicado(self):
        self.criar_saldo()

        with self.assertRaises(ValidationError):
            self.criar_saldo()

    def test_constraint_impede_saldo_duplicado_no_banco(self):
        self.criar_saldo()

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                SaldoEstoque.objects.bulk_create([
                    SaldoEstoque(
                        matriz=self.matriz,
                        loja=self.loja,
                        produto=self.produto,
                        quantidade_atual=Decimal('0.000'),
                    )
                ])

    def test_rejeita_loja_de_outra_matriz(self):
        outra_matriz = Matriz.objects.create(
            nome='Outra Matriz'
        )

        outra_loja = Loja.objects.create(
            matriz=outra_matriz,
            nome='Outra Loja',
            status=StatusOperacional.ATIVA,
        )

        saldo = SaldoEstoque(
            matriz=self.matriz,
            loja=outra_loja,
            produto=self.produto,
        )

        with self.assertRaises(ValidationError) as contexto:
            saldo.full_clean()

        self.assertIn(
            'loja',
            contexto.exception.message_dict
        )

    def test_rejeita_produto_de_outra_matriz(self):
        outra_matriz = Matriz.objects.create(
            nome='Outra Matriz Produto'
        )

        outra_unidade = UnidadeMedida.objects.create(
            matriz=outra_matriz,
            sigla='CX',
            descricao='Caixa',
        )

        outro_produto = Produto.objects.create(
            matriz=outra_matriz,
            unidade_medida=outra_unidade,
            codigo_interno='OUT-001',
            nome='Outro Produto',
        )

        saldo = SaldoEstoque(
            matriz=self.matriz,
            loja=self.loja,
            produto=outro_produto,
        )

        with self.assertRaises(ValidationError) as contexto:
            saldo.full_clean()

        self.assertIn(
            'produto',
            contexto.exception.message_dict
        )

    def test_rejeita_produto_que_nao_controla_estoque(self):
        produto_sem_estoque = Produto.objects.create(
            matriz=self.matriz,
            unidade_medida=self.unidade,
            codigo_interno='SEM-EST-001',
            nome='Produto sem controle de estoque',
            controla_estoque=False,
        )

        saldo = SaldoEstoque(
            matriz=self.matriz,
            loja=self.loja,
            produto=produto_sem_estoque,
        )

        with self.assertRaises(ValidationError) as contexto:
            saldo.full_clean()

        self.assertIn(
            'produto',
            contexto.exception.message_dict
        )

        self.assertIn(
            'não controla estoque',
            contexto.exception.message_dict['produto'][0]
        )

    def test_save_rejeita_produto_que_nao_controla_estoque(self):
        produto_sem_estoque = Produto.objects.create(
            matriz=self.matriz,
            unidade_medida=self.unidade,
            codigo_interno='SEM-EST-002',
            nome='Outro produto sem controle de estoque',
            controla_estoque=False,
        )

        with self.assertRaises(ValidationError):
            SaldoEstoque.objects.create(
                matriz=self.matriz,
                loja=self.loja,
                produto=produto_sem_estoque,
            )

    def test_relacao_com_matriz_e_protegida(self):
        saldo = self.criar_saldo()

        with self.assertRaises(ProtectedError):
            saldo.matriz.delete()

    def test_relacao_com_loja_e_protegida(self):
        saldo = self.criar_saldo()

        with self.assertRaises(ProtectedError):
            saldo.loja.delete()

    def test_relacao_com_produto_e_protegida(self):
        saldo = self.criar_saldo()

        with self.assertRaises(ProtectedError):
            saldo.produto.delete()

    def test_string_do_saldo(self):
        saldo = self.criar_saldo(
            quantidade_atual=Decimal('7.500')
        )

        self.assertEqual(
            str(saldo),
            'Loja Estoque - EST-001 - 7.500'
        )

class MovimentacaoEstoqueModelTestCase(TestCase):
    def setUp(self):
        self.matriz = Matriz.objects.create(
            nome='Matriz Movimentação'
        )

        self.loja = Loja.objects.create(
            matriz=self.matriz,
            nome='Loja Movimentação',
            status=StatusOperacional.ATIVA,
        )

        self.unidade = UnidadeMedida.objects.create(
            matriz=self.matriz,
            sigla='UN',
            descricao='Unidade',
        )

        self.produto = Produto.objects.create(
            matriz=self.matriz,
            unidade_medida=self.unidade,
            codigo_interno='MOV-001',
            nome='Produto Movimentação',
            controla_estoque=True,
        )

    def criar_movimentacao(self, **dados):
        padrao = {
            'matriz': self.matriz,
            'loja': self.loja,
            'produto': self.produto,
            'tipo': TipoMovimentacao.ENTRADA_MANUAL,
            'natureza': NaturezaMovimentacao.ENTRADA,
            'quantidade': Decimal('5.000'),
            'saldo_anterior': Decimal('0.000'),
            'saldo_posterior': Decimal('5.000'),
            'origem': OrigemMovimentacao.MANUAL,
        }

        padrao.update(dados)

        return MovimentacaoEstoque.objects.create(**padrao)

    def test_cria_movimentacao_valida_de_entrada(self):
        movimentacao = self.criar_movimentacao()

        self.assertIsNotNone(movimentacao.uuid)
        self.assertEqual(
            movimentacao.natureza,
            NaturezaMovimentacao.ENTRADA
        )
        self.assertEqual(
            movimentacao.saldo_posterior,
            Decimal('5.000')
        )

    def test_cria_movimentacao_valida_de_saida(self):
        movimentacao = self.criar_movimentacao(
            tipo=TipoMovimentacao.SAIDA_MANUAL,
            natureza=NaturezaMovimentacao.SAIDA,
            quantidade=Decimal('2.000'),
            saldo_anterior=Decimal('5.000'),
            saldo_posterior=Decimal('3.000'),
        )

        self.assertEqual(
            movimentacao.saldo_posterior,
            Decimal('3.000')
        )

    def test_rejeita_quantidade_zero(self):
        with self.assertRaises(ValidationError):
            self.criar_movimentacao(
                quantidade=Decimal('0.000'),
                saldo_posterior=Decimal('0.000'),
            )

    def test_rejeita_quantidade_negativa(self):
        with self.assertRaises(ValidationError):
            self.criar_movimentacao(
                quantidade=Decimal('-1.000'),
            )

    def test_rejeita_saldo_anterior_negativo(self):
        with self.assertRaises(ValidationError):
            self.criar_movimentacao(
                saldo_anterior=Decimal('-1.000'),
                saldo_posterior=Decimal('4.000'),
            )

    def test_rejeita_saldo_posterior_negativo(self):
        with self.assertRaises(ValidationError):
            self.criar_movimentacao(
                tipo=TipoMovimentacao.SAIDA_MANUAL,
                natureza=NaturezaMovimentacao.SAIDA,
                quantidade=Decimal('2.000'),
                saldo_anterior=Decimal('1.000'),
                saldo_posterior=Decimal('-1.000'),
            )

    def test_rejeita_tipo_e_natureza_incompativeis(self):
        with self.assertRaises(ValidationError) as contexto:
            self.criar_movimentacao(
                tipo=TipoMovimentacao.COMPRA,
                natureza=NaturezaMovimentacao.SAIDA,
                saldo_anterior=Decimal('10.000'),
                saldo_posterior=Decimal('5.000'),
            )

        self.assertIn(
            'natureza',
            contexto.exception.message_dict
        )

    def test_rejeita_equacao_de_saldo_incorreta(self):
        with self.assertRaises(ValidationError) as contexto:
            self.criar_movimentacao(
                saldo_posterior=Decimal('8.000'),
            )

        self.assertIn(
            'saldo_posterior',
            contexto.exception.message_dict
        )

    def test_rejeita_loja_de_outra_matriz(self):
        outra_matriz = Matriz.objects.create(
            nome='Outra Matriz Movimentação'
        )

        outra_loja = Loja.objects.create(
            matriz=outra_matriz,
            nome='Outra Loja Movimentação',
            status=StatusOperacional.ATIVA,
        )

        with self.assertRaises(ValidationError):
            self.criar_movimentacao(
                loja=outra_loja,
            )

    def test_rejeita_produto_de_outra_matriz(self):
        outra_matriz = Matriz.objects.create(
            nome='Matriz de Outro Produto'
        )

        outra_unidade = UnidadeMedida.objects.create(
            matriz=outra_matriz,
            sigla='CX',
            descricao='Caixa',
        )

        outro_produto = Produto.objects.create(
            matriz=outra_matriz,
            unidade_medida=outra_unidade,
            codigo_interno='MOV-OUT-001',
            nome='Produto de outra matriz',
        )

        with self.assertRaises(ValidationError):
            self.criar_movimentacao(
                produto=outro_produto,
            )

    def test_rejeita_produto_sem_controle_de_estoque(self):
        produto_sem_estoque = Produto.objects.create(
            matriz=self.matriz,
            unidade_medida=self.unidade,
            codigo_interno='MOV-SEM-001',
            nome='Produto sem estoque',
            controla_estoque=False,
        )

        with self.assertRaises(ValidationError):
            self.criar_movimentacao(
                produto=produto_sem_estoque,
            )

    def test_impede_chave_idempotente_duplicada(self):
        self.criar_movimentacao(
            chave_idempotencia='manual:teste:001'
        )

        with self.assertRaises(ValidationError):
            self.criar_movimentacao(
                chave_idempotencia='manual:teste:001'
            )

    def test_constraint_impede_idempotencia_duplicada(self):
        self.criar_movimentacao(
            chave_idempotencia='integracao:001'
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                MovimentacaoEstoque.objects.bulk_create([
                    MovimentacaoEstoque(
                        matriz=self.matriz,
                        loja=self.loja,
                        produto=self.produto,
                        tipo=TipoMovimentacao.ENTRADA_MANUAL,
                        natureza=NaturezaMovimentacao.ENTRADA,
                        quantidade=Decimal('1.000'),
                        saldo_anterior=Decimal('5.000'),
                        saldo_posterior=Decimal('6.000'),
                        origem=OrigemMovimentacao.MANUAL,
                        chave_idempotencia='integracao:001',
                    )
                ])

    def test_permite_multiplas_chaves_vazias(self):
        primeira = self.criar_movimentacao()

        segunda = self.criar_movimentacao(
            quantidade=Decimal('1.000'),
            saldo_anterior=Decimal('5.000'),
            saldo_posterior=Decimal('6.000'),
        )

        self.assertNotEqual(
            primeira.pk,
            segunda.pk
        )

    def test_movimentacao_nao_pode_ser_editada(self):
        movimentacao = self.criar_movimentacao()

        movimentacao.observacao = 'Tentativa de edição'

        with self.assertRaises(ValidationError):
            movimentacao.save()

    def test_queryset_update_nao_pode_alterar_movimentacao(self):
        movimentacao = self.criar_movimentacao()

        with self.assertRaises(ValidationError):
            MovimentacaoEstoque.objects.filter(
                pk=movimentacao.pk
            ).update(
                observacao='Alteração indevida'
            )

    def test_queryset_delete_nao_pode_excluir_movimentacao(self):
        movimentacao = self.criar_movimentacao()

        with self.assertRaises(ValidationError):
            MovimentacaoEstoque.objects.filter(
                pk=movimentacao.pk
            ).delete()

        self.assertTrue(
            MovimentacaoEstoque.objects.filter(
                pk=movimentacao.pk
            ).exists()
        )

    def test_bulk_update_nao_pode_alterar_movimentacao(self):
        movimentacao = self.criar_movimentacao()
        movimentacao.observacao = 'Alteração indevida'

        with self.assertRaises(ValidationError):
            MovimentacaoEstoque.objects.bulk_update(
                [movimentacao],
                ['observacao'],
            )

    def test_movimentacao_nao_pode_ser_excluida(self):
        movimentacao = self.criar_movimentacao()

        with self.assertRaises(ValidationError):
            movimentacao.delete()

    def test_cria_reversao_integral_valida(self):
        original = self.criar_movimentacao(
            tipo=TipoMovimentacao.SAIDA_MANUAL,
            natureza=NaturezaMovimentacao.SAIDA,
            quantidade=Decimal('2.000'),
            saldo_anterior=Decimal('5.000'),
            saldo_posterior=Decimal('3.000'),
        )

        reversao = self.criar_movimentacao(
            tipo=TipoMovimentacao.REVERSAO_ENTRADA,
            natureza=NaturezaMovimentacao.ENTRADA,
            quantidade=Decimal('2.000'),
            saldo_anterior=Decimal('3.000'),
            saldo_posterior=Decimal('5.000'),
            origem=OrigemMovimentacao.SISTEMA,
            movimentacao_origem=original,
        )

        self.assertEqual(
            reversao.movimentacao_origem,
            original
        )

    def test_rejeita_reversao_com_quantidade_diferente(self):
        original = self.criar_movimentacao(
            tipo=TipoMovimentacao.SAIDA_MANUAL,
            natureza=NaturezaMovimentacao.SAIDA,
            quantidade=Decimal('2.000'),
            saldo_anterior=Decimal('5.000'),
            saldo_posterior=Decimal('3.000'),
        )

        with self.assertRaises(ValidationError):
            self.criar_movimentacao(
                tipo=TipoMovimentacao.REVERSAO_ENTRADA,
                natureza=NaturezaMovimentacao.ENTRADA,
                quantidade=Decimal('1.000'),
                saldo_anterior=Decimal('3.000'),
                saldo_posterior=Decimal('4.000'),
                origem=OrigemMovimentacao.SISTEMA,
                movimentacao_origem=original,
            )

    def test_impede_reversao_duplicada(self):
        original = self.criar_movimentacao(
            tipo=TipoMovimentacao.SAIDA_MANUAL,
            natureza=NaturezaMovimentacao.SAIDA,
            quantidade=Decimal('2.000'),
            saldo_anterior=Decimal('5.000'),
            saldo_posterior=Decimal('3.000'),
        )

        self.criar_movimentacao(
            tipo=TipoMovimentacao.REVERSAO_ENTRADA,
            natureza=NaturezaMovimentacao.ENTRADA,
            quantidade=Decimal('2.000'),
            saldo_anterior=Decimal('3.000'),
            saldo_posterior=Decimal('5.000'),
            origem=OrigemMovimentacao.SISTEMA,
            movimentacao_origem=original,
        )

        with self.assertRaises(ValidationError):
            self.criar_movimentacao(
                tipo=TipoMovimentacao.REVERSAO_ENTRADA,
                natureza=NaturezaMovimentacao.ENTRADA,
                quantidade=Decimal('2.000'),
                saldo_anterior=Decimal('3.000'),
                saldo_posterior=Decimal('5.000'),
                origem=OrigemMovimentacao.SISTEMA,
                movimentacao_origem=original,
            )

    def test_transferencia_exige_grupo(self):
        with self.assertRaises(ValidationError) as contexto:
            self.criar_movimentacao(
                tipo=TipoMovimentacao.TRANSFERENCIA_ENTRADA,
                natureza=NaturezaMovimentacao.ENTRADA,
                origem=OrigemMovimentacao.TRANSFERENCIA,
            )

        self.assertIn(
            'grupo_transferencia',
            contexto.exception.message_dict
        )

    def test_operacao_comum_rejeita_grupo_transferencia(self):
        with self.assertRaises(ValidationError):
            self.criar_movimentacao(
                grupo_transferencia=uuid.uuid4(),
            )

    def test_relacoes_principais_sao_protegidas(self):
        movimentacao = self.criar_movimentacao()

        with self.assertRaises(ProtectedError):
            movimentacao.matriz.delete()

        with self.assertRaises(ProtectedError):
            movimentacao.loja.delete()

        with self.assertRaises(ProtectedError):
            movimentacao.produto.delete()

    def test_string_da_movimentacao(self):
        movimentacao = self.criar_movimentacao()

        self.assertEqual(
            str(movimentacao),
            'MOV-001 - Entrada manual - 5.000'
        )



