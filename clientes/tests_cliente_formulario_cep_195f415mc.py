from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import NoReverseMatch, reverse

from clientes.forms import ClienteForm
from clientes.models import Cliente
from empresas.models import Matriz


class ContratoFormularioCliente195F415MCTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.matriz = Matriz.objects.first()

    def _base_pf(self):
        return {
            "tipo_pessoa": "PF",
            "nome": "Maria da Silva",
            "cpf": "529.982.247-25",
            "telefone": "11999999999",
            "data_nascimento": "",
            "email": "maria@example.com",
            "cep": "13280-000",
            "logradouro": "Rua Teste",
            "numero": "10",
            "complemento": "",
            "bairro": "Centro",
            "cidade": "Vinhedo",
            "uf": "SP",
            "aceita_email": True,
            "aceita_sms": False,
            "ativo": True,
        }

    def _base_pj(self):
        return {
            "tipo_pessoa": "PJ",
            "nome": "Empresa Exemplo",
            "cpf": "",
            "razao_social": "Empresa Exemplo Ltda",
            "nome_fantasia": "Empresa Exemplo",
            "cnpj": "04.252.011/0001-10",
            "inscricao_estadual": "",
            "contato_responsavel": "Maria",
            "telefone": "11999999999",
            "data_nascimento": "",
            "email": "empresa@example.com",
            "cep": "13280-000",
            "logradouro": "Rua Teste",
            "numero": "20",
            "complemento": "",
            "bairro": "Centro",
            "cidade": "Vinhedo",
            "uf": "SP",
            "aceita_email": True,
            "aceita_sms": False,
            "ativo": True,
        }

    def test_formulario_expoe_tipo_pessoa_documentos_e_endereco(self):
        form = ClienteForm()
        esperados = {
            "tipo_pessoa", "nome", "cpf", "data_nascimento",
            "razao_social", "nome_fantasia", "cnpj",
            "inscricao_estadual", "contato_responsavel",
            "telefone", "email", "cep", "logradouro", "numero",
            "complemento", "bairro", "cidade", "uf",
        }
        self.assertTrue(esperados.issubset(set(form.fields)))

    def test_formulario_pf_nao_exige_campos_pj(self):
        form = ClienteForm(data=self._base_pf())
        self.assertTrue(form.is_valid(), form.errors.as_json())

    def test_formulario_pj_nao_exige_cpf_nem_data_nascimento(self):
        form = ClienteForm(data=self._base_pj())
        self.assertTrue(form.is_valid(), form.errors.as_json())

    def test_formulario_normaliza_cep_para_oito_digitos(self):
        form = ClienteForm(data=self._base_pf())
        self.assertTrue(form.is_valid(), form.errors.as_json())
        self.assertEqual(form.cleaned_data["cep"], "13280000")

    def test_formulario_rejeita_cep_com_quantidade_incorreta(self):
        data = self._base_pf()
        data["cep"] = "1234"
        form = ClienteForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("cep", form.errors)

    def test_formulario_normal_nao_aceita_sentinela_consumidor(self):
        data = self._base_pf()
        data["cpf"] = "CONSUMIDOR"
        form = ClienteForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("cpf", form.errors)


class ContratoEndpointCep195F415MCTests(TestCase):
    def test_rota_consultar_cep_existe(self):
        try:
            url = reverse("clientes:consultar_cep")
        except NoReverseMatch as exc:
            self.fail(f"Rota clientes:consultar_cep ausente: {exc}")
        self.assertTrue(url)

    def test_servico_cep_existe_e_rejeita_formato_invalido_sem_rede(self):
        try:
            from clientes.services_cep import consultar_cep
        except Exception as exc:
            self.fail(f"Servico clientes.services_cep.consultar_cep ausente: {exc}")
        resultado = consultar_cep("1234")
        self.assertFalse(resultado.get("ok"))
        self.assertEqual(resultado.get("motivo"), "cep_invalido")

    def test_servico_cep_mapeia_endereco_do_provider(self):
        try:
            from clientes.services_cep import consultar_cep
        except Exception as exc:
            self.fail(f"Servico clientes.services_cep.consultar_cep ausente: {exc}")
        fake = {
            "cep": "13280-000",
            "logradouro": "Rua das Flores",
            "bairro": "Centro",
            "localidade": "Vinhedo",
            "uf": "SP",
        }
        with patch("clientes.services_cep._consultar_provider", return_value=fake):
            resultado = consultar_cep("13280-000")
        self.assertTrue(resultado["ok"])
        self.assertEqual(resultado["endereco"]["logradouro"], "Rua das Flores")
        self.assertEqual(resultado["endereco"]["bairro"], "Centro")
        self.assertEqual(resultado["endereco"]["cidade"], "Vinhedo")
        self.assertEqual(resultado["endereco"]["uf"], "SP")

    def test_servico_cep_falha_provider_retorna_falha_controlada(self):
        try:
            from clientes.services_cep import consultar_cep
        except Exception as exc:
            self.fail(f"Servico clientes.services_cep.consultar_cep ausente: {exc}")
        with patch("clientes.services_cep._consultar_provider", side_effect=OSError("offline")):
            resultado = consultar_cep("13280-000")
        self.assertFalse(resultado["ok"])
        self.assertEqual(resultado["motivo"], "provider_indisponivel")