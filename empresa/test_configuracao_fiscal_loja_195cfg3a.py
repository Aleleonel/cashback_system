from pathlib import Path

from django.test import SimpleTestCase

from empresa.forms import ConfiguracaoFiscalLojaEmpresaForm
from fiscal.models_emissao_fiscal import ConfiguracaoEmissaoFiscalLoja


class ConfiguracaoFiscalLojaEmpresaForm195CFG3ATests(SimpleTestCase):
    def test_form_aponta_para_modelo_fiscal_da_loja(self):
        self.assertIs(ConfiguracaoFiscalLojaEmpresaForm._meta.model, ConfiguracaoEmissaoFiscalLoja)

    def test_form_expoe_campos_operacionais_necessarios(self):
        esperados = {"razao_social", "nome_fantasia", "inscricao_estadual", "logradouro", "numero", "complemento", "bairro", "municipio", "codigo_municipio_ibge", "uf", "cep", "crt", "ambiente_nfce", "serie_nfce", "ativa"}
        self.assertEqual(set(ConfiguracaoFiscalLojaEmpresaForm._meta.fields), esperados)

    def test_template_integra_dados_filial_e_fiscal(self):
        template = (Path(__file__).resolve().parent / "templates" / "empresa" / "form_loja.html").read_text(encoding="utf-8")
        self.assertIn('data-configuracao-fiscal-loja="195cfg3a"', template)
        self.assertIn("Configuracao fiscal da filial", template)
        self.assertIn("fiscal_form.razao_social", template)
        self.assertIn("fiscal_form.codigo_municipio_ibge", template)
        self.assertIn("fiscal_form.ambiente_nfce", template)
        self.assertIn("fiscal_form.serie_nfce", template)
        self.assertIn('name="configurar_fiscal"', template)

    def test_view_preserva_isolamento_da_matriz_e_transacao(self):
        view = (Path(__file__).resolve().parent / "views" / "lojas.py").read_text(encoding="utf-8")
        self.assertIn("PERMISSAO_EMPRESA_LOJAS_GERENCIAR", view)
        self.assertIn("matriz=contexto['matriz']", view)
        self.assertIn("with transaction.atomic():", view)
        self.assertIn("salvar_configuracao_fiscal_loja_empresa", view)

    def test_service_exige_full_clean_antes_de_persistir(self):
        service = (Path(__file__).resolve().parent / "services.py").read_text(encoding="utf-8")
        self.assertIn("def salvar_configuracao_fiscal_loja_empresa(", service)
        self.assertIn("configuracao.full_clean()", service)
        self.assertIn('recurso="empresa.loja.configuracao_fiscal"', service)
