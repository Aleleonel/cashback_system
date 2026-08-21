from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from empresas.models import Loja, Matriz
from fiscal.choices_documento_fiscal import (
    AmbienteDocumentoFiscal,
    ModeloDocumentoFiscal,
)
from fiscal.models_emissao_fiscal import ConfiguracaoEmissaoFiscalLoja
from fiscal.services_preparacao_documento_fiscal import preparar_documento_fiscal
from pdv.models import Venda, VendaFiscal


class IntegracaoChavePreparacaoNFCeTests(TestCase):
    def setUp(self):
        self.matriz = Matriz.objects.create(nome="Matriz")
        self.loja = Loja.objects.create(
            matriz=self.matriz,
            nome="Loja",
            cnpj="12345678000195",
        )
        self.usuario = get_user_model().objects.create_user(
            username="operador_integracao_chave_nfce",
            password="senha-teste",
            matriz=self.matriz,
        )
        self.usuario.lojas.add(self.loja)

        ConfiguracaoEmissaoFiscalLoja.objects.create(
            loja=self.loja,
            razao_social="Loja Ltda",
            inscricao_estadual="123456789",
            logradouro="Rua A",
            numero="1",
            bairro="Centro",
            municipio="Sao Paulo",
            codigo_municipio_ibge="3550308",
            uf="SP",
            cep="01001000",
            crt="3",
            ambiente_nfce=AmbienteDocumentoFiscal.HOMOLOGACAO,
            serie_nfce=1,
        )
        self.venda = Venda.objects.create(
            matriz=self.matriz,
            loja=self.loja,
            operador=self.usuario,
            status="finalizada",
            tipo_emissao="fiscal",
            finalizada_em=datetime(
                2026, 8, 21, 18, 0, tzinfo=timezone.utc
            ),
            subtotal=Decimal("0.00"),
            desconto_geral=Decimal("0.00"),
            acrescimo_geral=Decimal("0.00"),
            total=Decimal("0.00"),
            uf_destino="SP",
        )
        self.venda_fiscal = VendaFiscal.objects.create(
            venda=self.venda,
            regime_tributario="normal",
            uf_origem="SP",
            uf_destino="SP",
            tipo_operacao="saida",
            finalidade_operacao="venda",
            contribuinte_icms=False,
            consumidor_final=True,
            total_base_operacao=Decimal("0.00"),
            total_base_icms=Decimal("0.00"),
            total_icms=Decimal("0.00"),
            total_fcp=Decimal("0.00"),
            total_base_pis=Decimal("0.00"),
            total_pis=Decimal("0.00"),
            total_base_cofins=Decimal("0.00"),
            total_cofins=Decimal("0.00"),
            total_base_ipi=Decimal("0.00"),
            total_ipi=Decimal("0.00"),
            total_tributos=Decimal("0.00"),
        )

    def _mock_payload_valido(self):
        return patch(
            "fiscal.services_preparacao_documento_fiscal."
            "validar_dados_documento_fiscal",
            return_value=None,
        )

    @patch(
        "fiscal.services_chave_acesso.secrets.randbelow",
        return_value=12345678,
    )
    def test_preparacao_nfce_gera_identidade_fiscal(self, mocked):
        with self._mock_payload_valido():
            documento, _, _ = preparar_documento_fiscal(
                venda_fiscal=self.venda_fiscal,
                modelo=ModeloDocumentoFiscal.NFCE,
                ambiente=AmbienteDocumentoFiscal.HOMOLOGACAO,
                serie=1,
            )

        self.assertEqual(documento.numero, 1)
        self.assertEqual(documento.codigo_numerico, "12345678")
        self.assertEqual(len(documento.chave_acesso), 44)
        self.assertEqual(len(documento.digito_verificador), 1)
        mocked.assert_called_once()

    @patch(
        "fiscal.services_chave_acesso.secrets.randbelow",
        side_effect=[12345678, 87654321],
    )
    def test_retry_preserva_numero_codigo_dv_e_chave(self, mocked):
        with self._mock_payload_valido():
            documento1, _, _ = preparar_documento_fiscal(
                venda_fiscal=self.venda_fiscal,
                modelo=ModeloDocumentoFiscal.NFCE,
                ambiente=AmbienteDocumentoFiscal.HOMOLOGACAO,
                serie=1,
            )
            identidade1 = (
                documento1.numero,
                documento1.codigo_numerico,
                documento1.digito_verificador,
                documento1.chave_acesso,
            )

            documento2, _, _ = preparar_documento_fiscal(
                venda_fiscal=self.venda_fiscal,
                modelo=ModeloDocumentoFiscal.NFCE,
                ambiente=AmbienteDocumentoFiscal.HOMOLOGACAO,
                serie=1,
            )
            identidade2 = (
                documento2.numero,
                documento2.codigo_numerico,
                documento2.digito_verificador,
                documento2.chave_acesso,
            )

        self.assertEqual(identidade1, identidade2)
        self.assertEqual(mocked.call_count, 1)

    @patch(
        "fiscal.services_chave_acesso.secrets.randbelow",
        return_value=12345678,
    )
    def test_chave_usa_data_fiscal_da_venda(self, mocked):
        with self._mock_payload_valido():
            documento, _, _ = preparar_documento_fiscal(
                venda_fiscal=self.venda_fiscal,
                modelo=ModeloDocumentoFiscal.NFCE,
                ambiente=AmbienteDocumentoFiscal.HOMOLOGACAO,
                serie=1,
            )

        self.assertTrue(documento.chave_acesso.startswith("352608"))
