from datetime import date
from django.test import TestCase
from empresas.models import Matriz, Loja
from clientes.models import Cliente
from relatorios.selectors import get_relatorio_aniversariantes

class RelatorioAniversariantesDerivadoClientesTests(TestCase):
    def setUp(self):
        self.matriz = Matriz.objects.create(nome="Matriz Aniv")
        self.outra_matriz = Matriz.objects.create(nome="Outra Matriz Aniv")
        self.loja = Loja.objects.create(matriz=self.matriz, nome="Loja Aniv")
        self.outra_loja = Loja.objects.create(matriz=self.outra_matriz, nome="Outra Loja Aniv")

    def cliente(self, nome, nascimento, matriz=None, loja=None, tipo="PF"):
        matriz = matriz or self.matriz
        loja = loja or self.loja
        return Cliente.objects.create(matriz=matriz, loja_cadastro=loja, nome=nome, tipo_pessoa=tipo, data_nascimento=nascimento)

    def test_relatorio_e_derivado_diretamente_de_cliente(self):
        cliente = self.cliente("Cliente Fonte", date(1990, 5, 10))
        resultado = get_relatorio_aniversariantes(matriz=self.matriz, mes=5)
        self.assertEqual(list(resultado), [cliente])
        self.assertIsInstance(resultado.first(), Cliente)

    def test_alteracao_no_cliente_reflete_no_relatorio_sem_cadastro_paralelo(self):
        cliente = self.cliente("Nome Antigo", date(1990, 5, 10))
        cliente.nome = "Nome Atualizado"
        cliente.telefone = "11999999999"
        cliente.save()
        atual = get_relatorio_aniversariantes(matriz=self.matriz, mes=5).get(pk=cliente.pk)
        self.assertEqual(atual.nome, "Nome Atualizado")
        self.assertEqual(atual.telefone, "11999999999")

    def test_filtra_mes_pf_e_exclui_outra_matriz(self):
        esperado = self.cliente("Ana", date(1990, 5, 10))
        self.cliente("Outro mes", date(1990, 6, 10))
        self.cliente("Outra matriz", date(1990, 5, 11), matriz=self.outra_matriz, loja=self.outra_loja)
        self.cliente("Empresa", None, tipo="PJ")
        ids = list(get_relatorio_aniversariantes(matriz=self.matriz, mes=5).values_list("id", flat=True))
        self.assertEqual(ids, [esperado.id])

    def test_ordena_por_dia_depois_nome(self):
        b = self.cliente("Bruna", date(1980, 5, 3))
        a = self.cliente("Ana", date(1981, 5, 3))
        c = self.cliente("Carla", date(1982, 5, 20))
        ids = list(get_relatorio_aniversariantes(matriz=self.matriz, mes=5).values_list("id", flat=True))
        self.assertEqual(ids, [a.id, b.id, c.id])
