from django.core.exceptions import ValidationError
from django.db.models.deletion import ProtectedError
from django.test import TestCase

from auditoria.models import RegistroAuditoria
from empresas.models import Matriz
from fiscal.forms_configuracao_fiscal import ConfiguracaoFiscalMatrizForm
from fiscal.models_configuracao_fiscal import ConfiguracaoFiscalMatriz
from fiscal.models_regra_fiscal import RegraFiscal
from fiscal.selectors_configuracao_fiscal import (
    get_configuracao_fiscal_matriz,
)
from fiscal.services_configuracao_fiscal import (
    atualizar_configuracao_fiscal_matriz,
    criar_configuracao_fiscal_matriz,
)


def dados_validos(**extras):
    dados = {
        "regime_tributario": RegraFiscal.REGIME_NORMAL,
        "uf_origem": "SP",
        "contribuinte_icms": True,
        "consumidor_final_padrao": True,
        "ativa": True,
        "observacoes": "Teste.",
    }
    dados.update(extras)
    return dados


class Base(TestCase):
    def setUp(self):
        self.matriz = Matriz.objects.create(
            nome="Matriz Fiscal",
            cnpj="12345678000199",
        )


class ModelTests(Base):
    def test_cria_e_normaliza_uf(self):
        config = ConfiguracaoFiscalMatriz.objects.create(
            matriz=self.matriz,
            **dados_validos(uf_origem=" sp "),
        )
        self.assertEqual(config.uf_origem, "SP")
        self.assertTrue(config.pronta_para_operacao)

    def test_rejeita_regime_invalido(self):
        config = ConfiguracaoFiscalMatriz(
            matriz=self.matriz,
            **dados_validos(regime_tributario="invalido"),
        )
        with self.assertRaises(ValidationError):
            config.full_clean()

    def test_rejeita_uf_invalida(self):
        config = ConfiguracaoFiscalMatriz(
            matriz=self.matriz,
            **dados_validos(uf_origem="XX"),
        )
        with self.assertRaises(ValidationError):
            config.full_clean()

    def test_impede_duplicidade(self):
        ConfiguracaoFiscalMatriz.objects.create(
            matriz=self.matriz,
            **dados_validos(),
        )
        duplicada = ConfiguracaoFiscalMatriz(
            matriz=self.matriz,
            **dados_validos(),
        )
        with self.assertRaises(ValidationError):
            duplicada.full_clean()

    def test_inativa_nao_esta_pronta(self):
        config = ConfiguracaoFiscalMatriz.objects.create(
            matriz=self.matriz,
            **dados_validos(ativa=False),
        )
        self.assertFalse(config.pronta_para_operacao)

    def test_protege_matriz(self):
        ConfiguracaoFiscalMatriz.objects.create(
            matriz=self.matriz,
            **dados_validos(),
        )
        with self.assertRaises(ProtectedError):
            self.matriz.delete()


class FormTests(Base):
    def test_normaliza_uf(self):
        form = ConfiguracaoFiscalMatrizForm(
            data=dados_validos(uf_origem=" rj "),
        )
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["uf_origem"], "RJ")

    def test_rejeita_uf_invalida(self):
        form = ConfiguracaoFiscalMatrizForm(
            data=dados_validos(uf_origem="ZZ"),
        )
        self.assertFalse(form.is_valid())
        self.assertIn("uf_origem", form.errors)


class SelectorTests(Base):
    def test_retorna_ativa(self):
        config = ConfiguracaoFiscalMatriz.objects.create(
            matriz=self.matriz,
            **dados_validos(),
        )
        self.assertEqual(
            get_configuracao_fiscal_matriz(matriz=self.matriz),
            config,
        )

    def test_ignora_inativa(self):
        ConfiguracaoFiscalMatriz.objects.create(
            matriz=self.matriz,
            **dados_validos(ativa=False),
        )
        self.assertIsNone(
            get_configuracao_fiscal_matriz(matriz=self.matriz)
        )


class ServiceTests(Base):
    def test_cria_e_audita(self):
        config = criar_configuracao_fiscal_matriz(
            matriz=self.matriz,
            dados=dados_validos(),
        )
        self.assertTrue(config.pk)
        self.assertTrue(
            RegistroAuditoria.objects.filter(
                matriz=self.matriz,
                acao=RegistroAuditoria.ACAO_CRIAR,
                recurso="fiscal.configuracao_fiscal_matriz",
                recurso_id=str(config.pk),
            ).exists()
        )

    def test_impede_duplicidade(self):
        criar_configuracao_fiscal_matriz(
            matriz=self.matriz,
            dados=dados_validos(),
        )
        with self.assertRaises(ValidationError):
            criar_configuracao_fiscal_matriz(
                matriz=self.matriz,
                dados=dados_validos(),
            )

    def test_atualiza_e_audita(self):
        config = criar_configuracao_fiscal_matriz(
            matriz=self.matriz,
            dados=dados_validos(),
        )
        atualizada = atualizar_configuracao_fiscal_matriz(
            configuracao=config,
            dados=dados_validos(
                regime_tributario=RegraFiscal.REGIME_SIMPLES,
                uf_origem="MG",
            ),
        )
        self.assertEqual(
            atualizada.regime_tributario,
            RegraFiscal.REGIME_SIMPLES,
        )
        self.assertEqual(atualizada.uf_origem, "MG")
        self.assertTrue(
            RegistroAuditoria.objects.filter(
                matriz=self.matriz,
                acao=RegistroAuditoria.ACAO_EDITAR,
                recurso="fiscal.configuracao_fiscal_matriz",
                recurso_id=str(config.pk),
            ).exists()
        )
