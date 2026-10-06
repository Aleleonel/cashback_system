from django.test import TestCase
from clientes.models import Cliente
from empresas.models import Loja, Matriz
from relatorios.selectors import get_relatorio_clientes


class RelatorioClientesSelectorTests(TestCase):
    def criar_matriz_loja(self, nome):
        matriz = Matriz.objects.create(nome=nome)
        loja = Loja.objects.create(matriz=matriz, nome='Loja ' + nome)
        return matriz, loja

    def test_isola_matriz_e_lista_clientes_da_matriz(self):
        m1, l1 = self.criar_matriz_loja('Matriz A F2EA05B')
        m2, l2 = self.criar_matriz_loja('Matriz B F2EA05B')
        c1 = Cliente.objects.create(matriz=m1, loja_cadastro=l1, nome='Cliente Alfa', ativo=True)
        Cliente.objects.create(matriz=m2, loja_cadastro=l2, nome='Cliente Intruso', ativo=True)
        ids = list(get_relatorio_clientes(matriz=m1).values_list('id', flat=True))
        self.assertEqual(ids, [c1.id])

    def test_filtra_ativo_e_inativo(self):
        m, loja = self.criar_matriz_loja('Matriz Status F2EA05B')
        ativo = Cliente.objects.create(matriz=m, loja_cadastro=loja, nome='Ativo', ativo=True)
        inativo = Cliente.objects.create(matriz=m, loja_cadastro=loja, nome='Inativo', ativo=False)
        self.assertEqual(list(get_relatorio_clientes(matriz=m, ativo=True).values_list('id', flat=True)), [ativo.id])
        self.assertEqual(list(get_relatorio_clientes(matriz=m, ativo=False).values_list('id', flat=True)), [inativo.id])

    def test_busca_por_nome(self):
        m, loja = self.criar_matriz_loja('Matriz Busca F2EA05B')
        alvo = Cliente.objects.create(matriz=m, loja_cadastro=loja, nome='Maria Relatorio', ativo=True)
        Cliente.objects.create(matriz=m, loja_cadastro=loja, nome='Joao Outro', ativo=True)
        ids = list(get_relatorio_clientes(matriz=m, busca='Maria').values_list('id', flat=True))
        self.assertEqual(ids, [alvo.id])

    def test_resultado_ordenado_por_nome(self):
        m, loja = self.criar_matriz_loja('Matriz Ordem F2EA05B')
        Cliente.objects.create(matriz=m, loja_cadastro=loja, nome='Zulu', ativo=True)
        Cliente.objects.create(matriz=m, loja_cadastro=loja, nome='Alfa', ativo=True)
        nomes = list(get_relatorio_clientes(matriz=m).values_list('nome', flat=True))
        self.assertEqual(nomes, ['Alfa', 'Zulu'])
