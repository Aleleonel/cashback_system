from django.core.exceptions import ValidationError
from django.db import models
from django.test import TestCase

from clientes.models import Cliente


class ClientePfPjEnderecoContratoTests(TestCase):
    CAMPOS_NOVOS = {
        "tipo_pessoa": models.CharField,
        "cnpj": models.CharField,
        "razao_social": models.CharField,
        "nome_fantasia": models.CharField,
        "inscricao_estadual": models.CharField,
        "contato_responsavel": models.CharField,
        "cep": models.CharField,
        "logradouro": models.CharField,
        "numero": models.CharField,
        "complemento": models.CharField,
        "bairro": models.CharField,
        "cidade": models.CharField,
        "uf": models.CharField,
    }

    def campo(self, nome):
        return Cliente._meta.get_field(nome)

    def cliente_base(self, **overrides):
        dados = {
                        "nome": "Cliente Teste",
            "cpf": "52998224725",
        }
        dados.update(overrides)
        return Cliente(**dados)

    def test_modelo_expoe_tipo_pessoa_e_campos_pf_pj_endereco(self):
        for nome, classe in self.CAMPOS_NOVOS.items():
            with self.subTest(campo=nome):
                campo = self.campo(nome)
                self.assertIsInstance(campo, classe)

    def test_tipo_pessoa_oferece_pf_e_pj(self):
        campo = self.campo("tipo_pessoa")
        choices = dict(campo.choices)
        self.assertIn("PF", choices)
        self.assertIn("PJ", choices)

    def test_tipo_pessoa_legado_tem_default_pf(self):
        campo = self.campo("tipo_pessoa")
        self.assertEqual(campo.get_default(), "PF")

    def test_campos_endereco_suportam_contrato_cep(self):
        for nome in ("cep", "logradouro", "numero", "complemento", "bairro", "cidade", "uf"):
            with self.subTest(campo=nome):
                self.assertTrue(self.campo(nome).blank)

    def test_pf_exige_nome_e_cpf(self):
        cliente = self.cliente_base(tipo_pessoa="PF", nome="", cpf="")
        with self.assertRaises(ValidationError) as ctx:
            cliente.full_clean(exclude=["matriz", "loja_cadastro"], validate_unique=False, validate_constraints=False)
        self.assertIn("nome", ctx.exception.message_dict)
        self.assertIn("cpf", ctx.exception.message_dict)

    def test_pf_nao_exige_dados_juridicos(self):
        cliente = self.cliente_base(tipo_pessoa="PF")
        try:
            cliente.full_clean(exclude=["matriz", "loja_cadastro"], validate_unique=False, validate_constraints=False)
        except ValidationError as exc:
            juridicos = {"cnpj", "razao_social"} & set(exc.message_dict)
            self.assertFalse(juridicos, exc.message_dict)

    def test_pj_exige_razao_social_e_cnpj(self):
        cliente = self.cliente_base(
            tipo_pessoa="PJ",
            nome="Empresa Teste",
            cpf="",
            razao_social="",
            cnpj="",
        )
        with self.assertRaises(ValidationError) as ctx:
            cliente.full_clean(exclude=["matriz", "loja_cadastro"], validate_unique=False, validate_constraints=False)
        self.assertIn("razao_social", ctx.exception.message_dict)
        self.assertIn("cnpj", ctx.exception.message_dict)

    def test_pj_nao_exige_cpf(self):
        cliente = self.cliente_base(
            tipo_pessoa="PJ",
            nome="Empresa Teste",
            cpf="",
            razao_social="Empresa Teste Ltda",
            cnpj="11222333000181",
        )
        try:
            cliente.full_clean(exclude=["matriz", "loja_cadastro"], validate_unique=False, validate_constraints=False)
        except ValidationError as exc:
            self.assertNotIn("cpf", exc.message_dict, exc.message_dict)

    def test_numero_endereco_e_textual_para_aceitar_sn(self):
        campo = self.campo("numero")
        self.assertIsInstance(campo, models.CharField)
