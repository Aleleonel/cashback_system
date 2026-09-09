from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from clientes.models import Cliente
from empresas.models import Matriz, Loja


class ClienteDocumentosPfPjContratoTests(TestCase):
    def setUp(self):
        self.matriz = Matriz.objects.create(nome="Matriz CF")
        self.loja = Loja.objects.create(matriz=self.matriz, nome="Loja CF")

    def base(self, **kwargs):
        dados = dict(
            matriz=self.matriz,
            loja_cadastro=self.loja,
            nome="Cliente Teste",
            telefone="",
            email="",
        )
        dados.update(kwargs)
        return Cliente(**dados)

    def validar(self, cliente):
        cliente.full_clean(
            exclude=["matriz", "loja_cadastro"],
            validate_unique=False,
            validate_constraints=False,
        )

    def test_pf_rejeita_cpf_com_quantidade_incorreta_de_digitos(self):
        c = self.base(tipo_pessoa="PF", cpf="123")
        with self.assertRaises(ValidationError) as ctx:
            self.validar(c)
        self.assertIn("cpf", ctx.exception.message_dict)

    def test_pj_rejeita_cnpj_com_quantidade_incorreta_de_digitos(self):
        c = self.base(
            tipo_pessoa="PJ", cpf="", razao_social="Empresa Teste Ltda",
            cnpj="123"
        )
        with self.assertRaises(ValidationError) as ctx:
            self.validar(c)
        self.assertIn("cnpj", ctx.exception.message_dict)

    def test_pj_rejeita_cnpj_de_14_digitos_invalido(self):
        c = self.base(
            tipo_pessoa="PJ", cpf="", razao_social="Empresa Teste Ltda",
            cnpj="11111111111111"
        )
        with self.assertRaises(ValidationError) as ctx:
            self.validar(c)
        self.assertIn("cnpj", ctx.exception.message_dict)

    def test_dois_pj_sem_cpf_na_mesma_matriz_nao_colidem_por_cpf(self):
        Cliente.objects.create(
            matriz=self.matriz, loja_cadastro=self.loja, nome="PJ Um",
            tipo_pessoa="PJ", cpf="", razao_social="PJ Um Ltda",
            cnpj="11222333000181"
        )
        try:
            with transaction.atomic():
                Cliente.objects.create(
                    matriz=self.matriz, loja_cadastro=self.loja, nome="PJ Dois",
                    tipo_pessoa="PJ", cpf="", razao_social="PJ Dois Ltda",
                    cnpj="11444777000161"
                )
        except IntegrityError as exc:
            self.fail("Dois PJ sem CPF colidiram na constraint de CPF: %s" % exc)

    def test_cnpj_deve_ser_unico_por_matriz(self):
        Cliente.objects.create(
            matriz=self.matriz, loja_cadastro=self.loja, nome="PJ Um",
            tipo_pessoa="PJ", cpf="", razao_social="PJ Um Ltda",
            cnpj="11222333000181"
        )
        c = self.base(
            tipo_pessoa="PJ", cpf="", nome="PJ Duplicado",
            razao_social="PJ Duplicado Ltda", cnpj="11222333000181"
        )
        with self.assertRaises(ValidationError) as ctx:
            c.full_clean(exclude=["matriz", "loja_cadastro"])
        self.assertIn("cnpj", ctx.exception.message_dict)

    def test_consumidor_tecnico_legado_continua_representavel(self):
        c = self.base(tipo_pessoa="PF", nome="CONSUMIDOR", cpf="CONSUMIDOR")
        # O registro técnico legado não deve ser convertido em CPF artificial.
        self.assertEqual(c.cpf, "CONSUMIDOR")