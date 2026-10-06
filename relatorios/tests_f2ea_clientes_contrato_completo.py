from django.test import TestCase
from empresas.models import Loja, Matriz
from clientes.models import Cliente
from relatorios.selectors import get_relatorio_clientes

class RelatorioClientesContratoCompletoTests(TestCase):
    def setUp(self):
        self.matriz = Matriz.objects.create(nome='Matriz Contrato F2EA10')
        self.loja_a = Loja.objects.create(matriz=self.matriz, nome='Loja A F2EA10')
        self.loja_b = Loja.objects.create(matriz=self.matriz, nome='Loja B F2EA10')
        self.pf = Cliente.objects.create(matriz=self.matriz, loja_cadastro=self.loja_a, nome='Maria Silva', cpf='11111111111', telefone='11999990001', email='maria@example.com', tipo_pessoa='PF', ativo=True)
        self.pj = Cliente.objects.create(matriz=self.matriz, loja_cadastro=self.loja_b, nome='Empresa Beta', cnpj='12345678000190', telefone='11988880002', email='contato@beta.com', tipo_pessoa='PJ', ativo=True)

    def test_filtra_tipo_pessoa(self):
        self.assertEqual(list(get_relatorio_clientes(matriz=self.matriz, tipo_pessoa='PF').values_list('id', flat=True)), [self.pf.id])
        self.assertEqual(list(get_relatorio_clientes(matriz=self.matriz, tipo_pessoa='PJ').values_list('id', flat=True)), [self.pj.id])

    def test_filtra_loja_cadastro(self):
        self.assertEqual(list(get_relatorio_clientes(matriz=self.matriz, loja_id=self.loja_a.id).values_list('id', flat=True)), [self.pf.id])
        self.assertEqual(list(get_relatorio_clientes(matriz=self.matriz, loja_id=self.loja_b.id).values_list('id', flat=True)), [self.pj.id])

    def test_busca_reutiliza_identificadores_e_contato(self):
        casos = [('11111111111', self.pf.id), ('12345678000190', self.pj.id), ('11999990001', self.pf.id), ('maria@example.com', self.pf.id)]
        for termo, esperado in casos:
            with self.subTest(termo=termo):
                ids = list(get_relatorio_clientes(matriz=self.matriz, busca=termo).values_list('id', flat=True))
                self.assertEqual(ids, [esperado])
