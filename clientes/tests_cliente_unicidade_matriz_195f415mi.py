from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from clientes.forms import ClienteForm
from clientes.models import Cliente
from empresas.models import Matriz, Loja


def valido_cpf():
    return "52998224725"


def outro_cpf():
    return "11144477735"


def valido_cnpj():
    return "11222333000181"


class ClienteUnicidadeNormalizada195F415MI(TestCase):
    def setUp(self):
        # Avoid depending on exact required fields of Matriz/Loja: inspect existing
        # project fixtures/factories through model defaults where possible.
        self.m1 = Matriz.objects.create(nome="Matriz MI 1")
        self.m2 = Matriz.objects.create(nome="Matriz MI 2")
        self.l1 = Loja.objects.create(matriz=self.m1, nome="Loja MI 1")
        self.l2 = Loja.objects.create(matriz=self.m2, nome="Loja MI 2")

    def test_pf_mesma_matriz_cpf_formatado_vs_digitos_rejeita_no_clean(self):
        Cliente.objects.create(matriz=self.m1, loja_cadastro=self.l1, nome="Cliente Um", cpf=valido_cpf())
        c = Cliente(matriz=self.m1, loja_cadastro=self.l1, nome="Cliente Dois", cpf="529.982.247-25")
        with self.assertRaises(ValidationError) as ctx:
            c.full_clean()
        self.assertIn("cpf", ctx.exception.message_dict)

    def test_pf_mesmo_cpf_matrizes_diferentes_permitido(self):
        Cliente.objects.create(matriz=self.m1, loja_cadastro=self.l1, nome="Cliente Um", cpf=valido_cpf())
        c = Cliente(matriz=self.m2, loja_cadastro=self.l2, nome="Cliente Dois", cpf="529.982.247-25")
        c.full_clean()
        c.save()
        self.assertEqual(c.cpf_normalizado, valido_cpf())

    def test_pj_mesma_matriz_cnpj_formatado_vs_digitos_rejeita_no_clean(self):
        Cliente.objects.create(
            matriz=self.m1, loja_cadastro=self.l1, tipo_pessoa="PJ", nome="Empresa Um",
            razao_social="Empresa Um LTDA", cnpj=valido_cnpj()
        )
        c = Cliente(
            matriz=self.m1, loja_cadastro=self.l1, tipo_pessoa="PJ", nome="Empresa Dois",
            razao_social="Empresa Dois LTDA", cnpj="11.222.333/0001-81"
        )
        with self.assertRaises(ValidationError) as ctx:
            c.full_clean()
        self.assertIn("cnpj", ctx.exception.message_dict)

    def test_pj_mesmo_cnpj_matrizes_diferentes_permitido(self):
        Cliente.objects.create(
            matriz=self.m1, loja_cadastro=self.l1, tipo_pessoa="PJ", nome="Empresa Um",
            razao_social="Empresa Um LTDA", cnpj=valido_cnpj()
        )
        c = Cliente(
            matriz=self.m2, loja_cadastro=self.l2, tipo_pessoa="PJ", nome="Empresa Dois",
            razao_social="Empresa Dois LTDA", cnpj="11.222.333/0001-81"
        )
        c.full_clean()
        c.save()
        self.assertEqual(c.cnpj_normalizado, valido_cnpj())

    def test_save_persiste_documentos_normalizados(self):
        pf = Cliente.objects.create(matriz=self.m1, loja_cadastro=self.l1, nome="Cliente PF", cpf="529.982.247-25")
        pj = Cliente.objects.create(
            matriz=self.m1, loja_cadastro=self.l1, tipo_pessoa="PJ", nome="Empresa PJ",
            razao_social="Empresa PJ LTDA", cnpj="11.222.333/0001-81"
        )
        self.assertEqual(pf.cpf_normalizado, valido_cpf())
        self.assertEqual(pj.cnpj_normalizado, valido_cnpj())


class ClienteFormContextoMatriz195F415MI(TestCase):
    def test_form_pf_duplicado_com_matriz_no_instance_rejeita_antes_do_save(self):
        m = Matriz.objects.create(nome="Matriz Form MI")
        loja = Loja.objects.create(matriz=m, nome="Loja Form MI")
        Cliente.objects.create(matriz=m, loja_cadastro=loja, nome="Cliente Existente", cpf=valido_cpf())
        form = ClienteForm(data={
            "tipo_pessoa": "PF", "nome": "Cliente Novo",
            "cpf": "529.982.247-25", "telefone": "", "email": "",
            "cep": "", "ativo": "on",
        })
        form.instance.matriz = m
        form.instance.loja_cadastro = loja
        self.assertFalse(form.is_valid())
        self.assertIn("cpf", form.errors)
