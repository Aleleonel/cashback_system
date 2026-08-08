from pathlib import Path

from django.test import TestCase

from empresas.models import Matriz
from fiscal.models_configuracao_fiscal import ConfiguracaoFiscalMatriz
from fiscal.models_regra_fiscal import RegraFiscal
from fiscal.selectors_configuracao_fiscal import (
    get_configuracao_fiscal_matriz,
    get_configuracao_fiscal_matriz_para_edicao,
)


class SelectorAdministrativoConfiguracaoFiscalTests(TestCase):
    def setUp(self):
        self.matriz = Matriz.objects.create(
            nome="Matriz UI Fiscal",
            cnpj="33333333000191",
        )

    def test_selector_administrativo_retorna_ativa(self):
        configuracao = ConfiguracaoFiscalMatriz.objects.create(
            matriz=self.matriz,
            regime_tributario=RegraFiscal.REGIME_NORMAL,
            uf_origem="SP",
            contribuinte_icms=True,
            consumidor_final_padrao=True,
            ativa=True,
        )

        self.assertEqual(
            get_configuracao_fiscal_matriz_para_edicao(
                matriz=self.matriz,
            ),
            configuracao,
        )

    def test_selector_administrativo_retorna_inativa(self):
        configuracao = ConfiguracaoFiscalMatriz.objects.create(
            matriz=self.matriz,
            regime_tributario=RegraFiscal.REGIME_NORMAL,
            uf_origem="SP",
            contribuinte_icms=True,
            consumidor_final_padrao=True,
            ativa=False,
        )

        self.assertEqual(
            get_configuracao_fiscal_matriz_para_edicao(
                matriz=self.matriz,
            ),
            configuracao,
        )
        self.assertIsNone(
            get_configuracao_fiscal_matriz(
                matriz=self.matriz,
            )
        )


class ContratoInterfaceConfiguracaoFiscalTests(TestCase):
    def test_arquivos_e_contratos_da_interface(self):
        raiz = Path(__file__).resolve().parents[1]

        urls = (raiz / "urls.py").read_text(encoding="utf-8")
        view = (
            raiz / "views_configuracao_fiscal.py"
        ).read_text(encoding="utf-8")
        template = (
            raiz
            / "templates"
            / "fiscal"
            / "configuracao_fiscal_matriz"
            / "form.html"
        ).read_text(encoding="utf-8")
        inicio = (
            raiz
            / "templates"
            / "fiscal"
            / "inicio.html"
        ).read_text(encoding="utf-8")
        views_principal = (
            raiz / "views.py"
        ).read_text(encoding="utf-8")

        self.assertIn(
            'name="configuracao_fiscal_matriz"',
            urls,
        )
        self.assertIn(
            "@require_permission(PERMISSAO_FISCAL_CONFIGURAR)",
            view,
        )
        self.assertIn(
            "get_contexto_operacional_usuario",
            view,
        )
        self.assertIn(
            "criar_configuracao_fiscal_matriz",
            view,
        )
        self.assertIn(
            "atualizar_configuracao_fiscal_matriz",
            view,
        )
        self.assertNotIn(
            "objects.create(",
            view,
        )
        self.assertIn(
            "Salvar configuração",
            template,
        )
        self.assertNotIn(
            'name="matriz"',
            template,
        )
        self.assertIn(
            "fiscal:configuracao_fiscal_matriz",
            inicio,
        )
        self.assertIn(
            "{% if pode_configurar %}",
            inicio,
        )
        self.assertIn(
            '"pode_configurar": pode_configurar',
            views_principal,
        )
