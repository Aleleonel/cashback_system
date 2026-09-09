from django.test import TestCase
from empresas.models import Matriz, Loja
from clientes.models import Cliente

class InvarianteModeloTipo195F415MPJ(TestCase):
    def setUp(self):
        self.matriz = Matriz.objects.create(nome="Matriz MPJ")
        self.loja = Loja.objects.create(matriz=self.matriz, nome="Loja MPJ")

    def test_save_pj_deve_limpar_campos_exclusivos_pf(self):
        c = Cliente(
            matriz=self.matriz, loja_cadastro=self.loja, tipo_pessoa="PJ",
            nome="Empresa MPJ", razao_social="Empresa MPJ Ltda",
            cnpj="11222333000181", cpf="52998224725",
        )
        c.save()
        c.refresh_from_db()
        self.assertEqual(c.cpf, "")
        self.assertEqual(c.cpf_normalizado, "")
        self.assertIsNone(c.data_nascimento)

    def test_save_pf_deve_limpar_campos_exclusivos_pj(self):
        c = Cliente(
            matriz=self.matriz, loja_cadastro=self.loja, tipo_pessoa="PF",
            nome="Maria Silva", cpf="52998224725",
            razao_social="Empresa Antiga Ltda", nome_fantasia="Antiga",
            cnpj="11222333000181", inscricao_estadual="123",
            contato_responsavel="Responsavel",
        )
        c.save()
        c.refresh_from_db()
        self.assertEqual(c.razao_social, "")
        self.assertEqual(c.nome_fantasia, "")
        self.assertEqual(c.cnpj, "")
        self.assertEqual(c.cnpj_normalizado, "")
        self.assertEqual(c.inscricao_estadual, "")
        self.assertEqual(c.contato_responsavel, "")