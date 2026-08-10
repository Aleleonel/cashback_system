from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.core.exceptions import ValidationError
from django.test import SimpleTestCase, TestCase

from fiscal.choices_documento_fiscal import (
    StatusDocumentoFiscal,
)
from fiscal.dto_documento_fiscal import (
    DadosDocumentoFiscal,
    DadosItemDocumentoFiscal,
)
from fiscal.services_preparacao_documento_fiscal import (
    gerar_idempotency_key_documento_fiscal,
    preparar_documento_fiscal,
    validar_dados_documento_fiscal,
)


def item_dto(**overrides):
    dados = dict(
        item_venda_id=1,
        origem_mercadoria_codigo="0",
        ncm_codigo="21069090",
        ncm_descricao="Teste",
        cest_codigo="",
        cfop_codigo="5102",
        cfop_descricao="Venda",
        cst_icms_codigo="00",
        csosn_codigo="",
        cst_pis_codigo="01",
        cst_cofins_codigo="01",
        cst_ipi_codigo="",
        regime_tributario="normal",
        uf_origem="SP",
        uf_destino="SP",
        tipo_operacao="saida",
        finalidade_operacao="venda",
        contribuinte_icms=False,
        consumidor_final=True,
        quantidade=Decimal("1.000"),
        valor_unitario=Decimal("10.00"),
        valor_produtos=Decimal("10.00"),
        desconto=Decimal("0.00"),
        acrescimo=Decimal("0.00"),
        frete=Decimal("0.00"),
        seguro=Decimal("0.00"),
        outras_despesas=Decimal("0.00"),
        base_operacao=Decimal("10.00"),
        base_icms=Decimal("10.00"),
        aliquota_icms=Decimal("18.0000"),
        valor_icms=Decimal("1.80"),
        base_fcp=Decimal("0.00"),
        aliquota_fcp=None,
        valor_fcp=Decimal("0.00"),
        base_pis=Decimal("10.00"),
        aliquota_pis=Decimal("1.6500"),
        valor_pis=Decimal("0.17"),
        base_cofins=Decimal("10.00"),
        aliquota_cofins=Decimal("7.6000"),
        valor_cofins=Decimal("0.76"),
        base_ipi=Decimal("0.00"),
        aliquota_ipi=None,
        valor_ipi=Decimal("0.00"),
        valor_total_tributos=Decimal("2.73"),
    )
    dados.update(overrides)
    return DadosItemDocumentoFiscal(**dados)


def documento_dto(**overrides):
    dados = dict(
        venda_fiscal_id=10,
        venda_id=20,
        matriz_id=30,
        loja_id=40,
        modelo="65",
        ambiente="homologacao",
        serie=1,
        numero=None,
        regime_tributario="normal",
        uf_origem="SP",
        uf_destino="SP",
        tipo_operacao="saida",
        finalidade_operacao="venda",
        contribuinte_icms=False,
        consumidor_final=True,
        total_base_operacao=Decimal("10.00"),
        total_base_icms=Decimal("10.00"),
        total_icms=Decimal("1.80"),
        total_fcp=Decimal("0.00"),
        total_base_pis=Decimal("10.00"),
        total_pis=Decimal("0.17"),
        total_base_cofins=Decimal("10.00"),
        total_cofins=Decimal("0.76"),
        total_base_ipi=Decimal("0.00"),
        total_ipi=Decimal("0.00"),
        total_tributos=Decimal("2.73"),
        itens=(item_dto(),),
    )
    dados.update(overrides)
    return DadosDocumentoFiscal(**dados)


class ContratoPreparacaoDocumentoFiscalTests(SimpleTestCase):
    def test_idempotency_key_e_deterministica(self):
        primeira = gerar_idempotency_key_documento_fiscal(
            venda_fiscal_id=10,
            modelo="65",
            ambiente="homologacao",
            serie=1,
        )
        segunda = gerar_idempotency_key_documento_fiscal(
            venda_fiscal_id=10,
            modelo="65",
            ambiente="homologacao",
            serie=1,
        )

        self.assertEqual(primeira, segunda)

    def test_idempotency_key_muda_com_intencao(self):
        primeira = gerar_idempotency_key_documento_fiscal(
            venda_fiscal_id=10,
            modelo="65",
            ambiente="homologacao",
            serie=1,
        )
        segunda = gerar_idempotency_key_documento_fiscal(
            venda_fiscal_id=10,
            modelo="55",
            ambiente="homologacao",
            serie=1,
        )

        self.assertNotEqual(primeira, segunda)

    def test_payload_valido(self):
        validar_dados_documento_fiscal(
            dados=documento_dto()
        )

    def test_payload_sem_itens_e_rejeitado(self):
        with self.assertRaises(ValidationError) as erro:
            validar_dados_documento_fiscal(
                dados=documento_dto(itens=())
            )

        self.assertIn(
            "itens",
            erro.exception.message_dict,
        )

    def test_payload_sem_ncm_e_rejeitado(self):
        with self.assertRaises(ValidationError):
            validar_dados_documento_fiscal(
                dados=documento_dto(
                    itens=(item_dto(ncm_codigo=""),)
                )
            )


class PrepararDocumentoFiscalServiceTests(TestCase):
    def venda_fiscal_fake(self):
        venda = SimpleNamespace(
            pk=20,
            matriz_id=30,
            loja_id=40,
        )

        return SimpleNamespace(
            pk=10,
            venda=venda,
        )

    def documento_fake(self, *, status, numero=None):
        documento = SimpleNamespace(
            pk=99,
            status=status,
            numero=numero,
            modelo="65",
            ambiente="homologacao",
            serie=1,
            matriz=SimpleNamespace(pk=30),
            loja=SimpleNamespace(pk=40),
            full_clean=MagicMock(),
        )

        return documento

    @patch(
        "fiscal.services_preparacao_documento_fiscal."
        "transicionar_documento_fiscal"
    )
    @patch(
        "fiscal.services_preparacao_documento_fiscal."
        "reservar_proximo_numero_documento_fiscal"
    )
    @patch(
        "fiscal.services_preparacao_documento_fiscal."
        "validar_dados_documento_fiscal"
    )
    @patch(
        "fiscal.services_preparacao_documento_fiscal."
        "construir_dados_documento_fiscal"
    )
    @patch(
        "fiscal.services_preparacao_documento_fiscal."
        "obter_ou_criar_documento_fiscal_rascunho"
    )
    def test_prepara_reservando_numero_apos_validacao(
        self,
        obter,
        construir,
        validar,
        reservar,
        transicionar,
    ):
        venda_fiscal = self.venda_fiscal_fake()
        documento = self.documento_fake(
            status=StatusDocumentoFiscal.RASCUNHO,
            numero=None,
        )

        obter.return_value = (documento, True)
        construir.side_effect = [
            documento_dto(numero=None),
            documento_dto(numero=123),
        ]
        reservar.return_value = 123

        manager = MagicMock()
        manager.select_for_update.return_value.get.return_value = (
            documento
        )

        with patch(
            "fiscal.services_preparacao_documento_fiscal."
            "DocumentoFiscal.objects",
            manager,
        ):
            retorno, dados, criado = preparar_documento_fiscal(
                venda_fiscal=venda_fiscal,
                modelo="65",
                ambiente="homologacao",
                serie=1,
            )

        self.assertIs(retorno, documento)
        self.assertTrue(criado)
        self.assertEqual(documento.numero, 123)
        self.assertEqual(dados.numero, 123)

        self.assertTrue(validar.called)
        reservar.assert_called_once()
        transicionar.assert_called_once()

        primeira_validacao = validar.call_args_list[0]
        self.assertIsNone(
            primeira_validacao.kwargs["dados"].numero
        )

    @patch(
        "fiscal.services_preparacao_documento_fiscal."
        "transicionar_documento_fiscal"
    )
    @patch(
        "fiscal.services_preparacao_documento_fiscal."
        "reservar_proximo_numero_documento_fiscal"
    )
    @patch(
        "fiscal.services_preparacao_documento_fiscal."
        "validar_dados_documento_fiscal"
    )
    @patch(
        "fiscal.services_preparacao_documento_fiscal."
        "construir_dados_documento_fiscal"
    )
    @patch(
        "fiscal.services_preparacao_documento_fiscal."
        "obter_ou_criar_documento_fiscal_rascunho"
    )
    def test_retry_preparado_nao_reserva_outro_numero(
        self,
        obter,
        construir,
        validar,
        reservar,
        transicionar,
    ):
        venda_fiscal = self.venda_fiscal_fake()
        documento = self.documento_fake(
            status=StatusDocumentoFiscal.PREPARADO,
            numero=123,
        )

        obter.return_value = (documento, False)
        construir.return_value = documento_dto(numero=123)

        manager = MagicMock()
        manager.select_for_update.return_value.get.return_value = (
            documento
        )

        with patch(
            "fiscal.services_preparacao_documento_fiscal."
            "DocumentoFiscal.objects",
            manager,
        ):
            retorno, dados, criado = preparar_documento_fiscal(
                venda_fiscal=venda_fiscal,
                modelo="65",
                ambiente="homologacao",
                serie=1,
            )

        self.assertIs(retorno, documento)
        self.assertFalse(criado)
        self.assertEqual(dados.numero, 123)
        reservar.assert_not_called()
        transicionar.assert_not_called()
        validar.assert_called_once()

    @patch(
        "fiscal.services_preparacao_documento_fiscal."
        "obter_ou_criar_documento_fiscal_rascunho"
    )
    def test_estado_invalido_bloqueia_preparacao(
        self,
        obter,
    ):
        venda_fiscal = self.venda_fiscal_fake()
        documento = self.documento_fake(
            status=StatusDocumentoFiscal.AUTORIZADO,
            numero=123,
        )

        obter.return_value = (documento, False)

        manager = MagicMock()
        manager.select_for_update.return_value.get.return_value = (
            documento
        )

        with patch(
            "fiscal.services_preparacao_documento_fiscal."
            "DocumentoFiscal.objects",
            manager,
        ):
            with self.assertRaises(ValidationError):
                preparar_documento_fiscal(
                    venda_fiscal=venda_fiscal,
                    modelo="65",
                    ambiente="homologacao",
                    serie=1,
                )