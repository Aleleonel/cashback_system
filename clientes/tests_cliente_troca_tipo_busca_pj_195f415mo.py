from django.test import TestCase
from clientes.forms import ClienteForm
from clientes.models import Cliente
from clientes.selectors import get_clientes_da_matriz, aplicar_busca_clientes
from empresas.models import Matriz, Loja

class TrocaTipoEBuscaPJ195F415MO(TestCase):
    def setUp(self):
        self.matriz=Matriz.objects.create(nome="Matriz MO")
        self.loja=Loja.objects.create(matriz=self.matriz,nome="Loja MO")

    def test_pf_para_pj_limpa_campos_exclusivos_pf(self):
        c=Cliente.objects.create(matriz=self.matriz,loja_cadastro=self.loja,nome="Pessoa Teste",cpf="52998224725",data_nascimento="1980-01-02")
        data={"tipo_pessoa":"PJ","nome":"","cpf":"52998224725","data_nascimento":"02/01/1980",
              "razao_social":"Empresa Nova Ltda","nome_fantasia":"Empresa Nova","cnpj":"11222333000181","cep":""}
        f=ClienteForm(data,instance=c);self.assertTrue(f.is_valid(),f.errors)
        obj=f.save()
        self.assertEqual(obj.cpf,"");self.assertEqual(obj.cpf_normalizado,"");self.assertIsNone(obj.data_nascimento)

    def test_pj_para_pf_limpa_campos_exclusivos_pj(self):
        c=Cliente.objects.create(matriz=self.matriz,loja_cadastro=self.loja,tipo_pessoa="PJ",nome="Empresa Antiga",cpf="",razao_social="Empresa Antiga Ltda",nome_fantasia="Antiga",cnpj="11222333000181",inscricao_estadual="123")
        data={"tipo_pessoa":"PF","nome":"Pessoa Nova","cpf":"52998224725","data_nascimento":"02/01/1980",
              "razao_social":"Empresa Antiga Ltda","nome_fantasia":"Antiga","cnpj":"11222333000181","inscricao_estadual":"123","cep":""}
        f=ClienteForm(data,instance=c);self.assertTrue(f.is_valid(),f.errors)
        obj=f.save()
        for campo in ("razao_social","nome_fantasia","cnpj","cnpj_normalizado","inscricao_estadual"):
            self.assertEqual(getattr(obj,campo),"")

    def test_busca_pj_por_cnpj_razao_e_fantasia(self):
        pj=Cliente.objects.create(matriz=self.matriz,loja_cadastro=self.loja,tipo_pessoa="PJ",nome="Comercial Aurora",cpf="",razao_social="Aurora Comercio de Suplementos Ltda",nome_fantasia="Comercial Aurora",cnpj="11222333000181")
        base=get_clientes_da_matriz(matriz=self.matriz)
        for termo in ("11222333000181","Aurora Comercio","Comercial Aurora"):
            ids=list(aplicar_busca_clientes(base,termo).values_list("id",flat=True))
            self.assertIn(pj.id,ids,termo)