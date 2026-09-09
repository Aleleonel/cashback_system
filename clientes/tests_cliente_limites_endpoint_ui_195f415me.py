from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from clientes.forms import ClienteForm
from clientes.models import Cliente
from clientes.services_cep import consultar_cep
from empresas.models import Matriz


class ContratosLimiteCliente195F415METests(TestCase):
    def _matriz(self, sufixo="1"):
        # Reuse the smallest viable factory shape dynamically from model defaults where possible.
        kwargs = {}
        for f in Matriz._meta.fields:
            if f.primary_key or getattr(f, "auto_created", False):
                continue
            if f.has_default() or f.null or f.blank:
                continue
            if f.name in ("nome", "razao_social", "nome_fantasia"):
                kwargs[f.name] = "Matriz Teste " + sufixo
            elif f.name == "cnpj":
                kwargs[f.name] = "1234567800019" + sufixo[-1]
        try:
            return Matriz.objects.create(**kwargs)
        except Exception:
            self.skipTest("Factory mínima de Matriz exige contrato específico já coberto por testes existentes.")

    def test_cep_em_branco_e_permitido(self):
        data = {"tipo_pessoa":"PF","nome":"Maria da Silva","cpf":"52998224725","cep":""}
        form = ClienteForm(data=data)
        self.assertTrue(form.is_valid(), form.errors.as_json())
        self.assertEqual(form.cleaned_data["cep"], "")

    def test_pj_sem_nome_canonico_deriva_nome_fantasia(self):
        data = {"tipo_pessoa":"PJ","nome":"","razao_social":"Empresa Exemplo LTDA",
                "nome_fantasia":"Exemplo","cnpj":"11222333000181","cep":""}
        form = ClienteForm(data=data)
        self.assertTrue(form.is_valid(), form.errors.as_json())
        self.assertEqual(form.cleaned_data["nome"], "Exemplo")

    def test_pj_sem_nome_e_sem_fantasia_deriva_razao_social(self):
        data = {"tipo_pessoa":"PJ","nome":"","razao_social":"Empresa Exemplo LTDA",
                "nome_fantasia":"","cnpj":"11222333000181","cep":""}
        form = ClienteForm(data=data)
        self.assertTrue(form.is_valid(), form.errors.as_json())
        self.assertEqual(form.cleaned_data["nome"], "Empresa Exemplo LTDA")

    @patch("clientes.services_cep._consultar_provider", return_value={"erro": True})
    def test_viacep_nao_encontrado_retorna_falha_controlada(self, _):
        r = consultar_cep("13280-000")
        self.assertFalse(r["ok"])
        self.assertIn(r["motivo"], ("cep_nao_encontrado", "nao_encontrado"))

    def test_endpoint_cep_exige_autenticacao(self):
        response = self.client.get(reverse("clientes:consultar_cep"), {"cep":"13280000"})
        self.assertIn(response.status_code, (302, 401, 403))

    @patch("clientes.views.consultar_cep", return_value={"ok":False,"motivo":"cep_invalido"})
    def test_endpoint_cep_invalido_retorna_json_controlado(self, _):
        User=get_user_model()
        fields={f.name for f in User._meta.fields}
        kwargs={}
        if "username" in fields: kwargs["username"]="teste_cep"
        if "email" in fields: kwargs["email"]="teste_cep@example.com"
        user=User.objects.create_user(password="SenhaTeste123!", **kwargs)
        self.client.force_login(user)
        response=self.client.get(reverse("clientes:consultar_cep"), {"cep":"123"})
        self.assertEqual(response.status_code,400)
        self.assertEqual(response.json().get("ok"),False)

    def test_form_template_contem_campos_pf_pj_e_endereco(self):
        from pathlib import Path
        template=Path("clientes/templates/clientes/form_cliente.html").read_text(encoding="utf-8")
        for token in ("tipo_pessoa","razao_social","cnpj","cep","logradouro","bairro","cidade","uf"):
            self.assertIn(token,template)


class UnicidadeNormalizadaCliente195F415METests(TestCase):
    def test_modelo_possui_constraints_normalizadas_pf_pj(self):
        nomes={c.name for c in Cliente._meta.constraints}
        self.assertIn("unique_cliente_pf_por_matriz_cpf_norm",nomes)
        self.assertIn("unique_cliente_pj_por_matriz_cnpj_norm",nomes)