from django.test import TestCase

from empresas.models import Matriz
from rh.models import Cargo, Departamento, Funcionario


class FuncionarioModelTests(TestCase):
    def setUp(self):
        self.matriz = Matriz.objects.create(
            nome="Matriz Teste",
        )
        self.cargo = Cargo.objects.create(
            matriz=self.matriz,
            nome="Analista",
        )
        self.departamento = Departamento.objects.create(
            matriz=self.matriz,
            nome="Administrativo",
        )

    def test_funcionario_pode_ser_criado(self):
        funcionario = Funcionario.objects.create(
            matriz=self.matriz,
            cargo=self.cargo,
            departamento=self.departamento,
            nome_completo="Funcionário Teste",
            cpf="12345678901",
            data_admissao="2026-07-22",
        )

        self.assertEqual(str(funcionario), "Funcionário Teste")
        self.assertTrue(funcionario.ativo)