from unittest.mock import patch
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from empresas.models import Loja, Matriz
from fiscal.choices_documento_fiscal import (
    AmbienteDocumentoFiscal,
    ModeloDocumentoFiscal,
    StatusDocumentoFiscal,
)
from fiscal.models import (
    CFOP,
    CSTCOFINS,
    CSTICMS,
    CSTPIS,
    NCM,
    OrigemMercadoria,
    RegraFiscal,
)
from fiscal.models_configuracao_fiscal import ConfiguracaoFiscalMatriz
from fiscal.models_emissao_fiscal import ConfiguracaoEmissaoFiscalLoja
from fiscal.services_assinatura_documento_fiscal import assinar_documento_fiscal
from fiscal.services_geracao_xml_documento_fiscal import (
    gerar_e_persistir_xml_rascunho_nfce,
)
from fiscal.services_preparacao_documento_fiscal import preparar_documento_fiscal
from pdv.choices import StatusOperacaoVenda, TipoEmissaoVenda
from pdv.models import (
    Caixa,
    FormaPagamento,
    ItemVenda,
    PagamentoVenda,
    SessaoCaixa,
    Venda,
    VendaFiscal,
)
from pdv.services.vendas.finalizacao import finalizar_venda
from produtos.models import Produto, UnidadeMedida


class IntegracaoPersistenciaXMLNFCeTests(TestCase):
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
            ativo=True,
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
        ConfiguracaoFiscalMatriz.objects.create(
            matriz=self.matriz,
            regime_tributario=RegraFiscal.REGIME_NORMAL,
            uf_origem="SP",
            contribuinte_icms=True,
            consumidor_final_padrao=True,
            ativa=True,
        )

        origem = OrigemMercadoria.objects.filter(codigo="0").first()
        ncm = NCM.objects.filter(codigo="21069090").first()
        cfop = CFOP.objects.filter(codigo="5102").first()
        cst_icms = CSTICMS.objects.filter(codigo="00").first()
        cst_pis = CSTPIS.objects.filter(codigo="01").first()
        cst_cofins = CSTCOFINS.objects.filter(codigo="01").first()

        self.assertIsNotNone(origem)
        self.assertIsNotNone(ncm)
        self.assertIsNotNone(cfop)
        self.assertIsNotNone(cst_icms)
        self.assertIsNotNone(cst_pis)
        self.assertIsNotNone(cst_cofins)

        regra = RegraFiscal.objects.create(
            codigo_interno="NFCE-INT-REGRA",
            nome="Regra integracao NFC-e",
            prioridade=10,
            ativo=True,
            matriz=self.matriz,
            loja=self.loja,
            regime_tributario=RegraFiscal.REGIME_NORMAL,
            tipo_operacao=RegraFiscal.TIPO_SAIDA,
            finalidade_operacao=RegraFiscal.FINALIDADE_VENDA,
            uf_origem="SP",
            uf_destino="SP",
            cfop=cfop,
            cst_icms=cst_icms,
            cst_pis=cst_pis,
            cst_cofins=cst_cofins,
            aliquota_icms=Decimal("18"),
            aliquota_fcp=Decimal("2"),
            aliquota_pis=Decimal("1.65"),
            aliquota_cofins=Decimal("7.60"),
        )

        unidade = UnidadeMedida.objects.create(
            matriz=self.matriz,
            sigla="UN",
            descricao="Unidade",
        )
        produto = Produto.objects.create(
            matriz=self.matriz,
            unidade_medida=unidade,
            codigo_interno="NFCE-INT-001",
            nome="Produto NFC-e Integracao",
            ncm=ncm.codigo,
            custo_base=Decimal("10.00"),
            preco_venda=Decimal("20.00"),
            controla_estoque=False,
            origem_mercadoria=origem,
            ncm_fiscal=ncm,
            cst_icms=cst_icms,
            cst_pis=cst_pis,
            cst_cofins=cst_cofins,
            regra_fiscal_padrao=regra,
        )

        caixa = Caixa.objects.create(
            matriz=self.matriz,
            loja=self.loja,
            nome="Caixa Integracao NFC-e",
            codigo="CX-NFCE-INT",
        )
        sessao = SessaoCaixa.objects.create(
            caixa=caixa,
            operador_abertura=self.usuario,
            valor_abertura=Decimal("0.00"),
        )

        self.venda = Venda.objects.create(
            matriz=self.matriz,
            loja=self.loja,
            sessao_caixa=sessao,
            operador=self.usuario,
            vendedor=self.usuario,
            status=StatusOperacaoVenda.ABERTA,
            tipo_emissao=TipoEmissaoVenda.FISCAL,
            uf_destino="SP",
        )

        ItemVenda.objects.create(
            venda=self.venda,
            produto=produto,
            sequencia=1,
            quantidade=Decimal("1.000"),
            preco_unitario=Decimal("20.00"),
            subtotal=Decimal("20.00"),
            total=Decimal("20.00"),
        )

        forma = FormaPagamento.objects.create(
            matriz=self.matriz,
            nome="PIX Integracao NFC-e",
            codigo="PIX",
            tipo="pix",
            ativa=True,
            movimenta_caixa=False,
            permite_troco=False,
        )
        pagamento = PagamentoVenda(
            venda=self.venda,
            forma_pagamento=forma,
            valor=Decimal("20.00"),
            parcelas=1,
        )
        pagamento.full_clean()
        pagamento.save()

        self.venda = finalizar_venda(
            venda=self.venda,
            usuario=self.usuario,
        )
        self.venda.refresh_from_db()

        self.assertEqual(
            self.venda.status,
            StatusOperacaoVenda.FINALIZADA,
        )
        self.assertIsNotNone(self.venda.finalizada_em)
        self.assertEqual(self.venda.total, Decimal("20.00"))
        self.assertTrue(
            hasattr(self.venda.itens.get(sequencia=1), "fiscal")
        )

        self.venda_fiscal = VendaFiscal.objects.get(
            venda=self.venda
        )

    @patch(
        "fiscal.services_chave_acesso.secrets.randbelow",
        return_value=12345678,
    )
    def test_persiste_xml_rascunho_em_documento_real(self, mocked):
        documento, _, _ = preparar_documento_fiscal(
            venda_fiscal=self.venda_fiscal,
            modelo=ModeloDocumentoFiscal.NFCE,
            ambiente=AmbienteDocumentoFiscal.HOMOLOGACAO,
            serie=1,
        )
        documento = gerar_e_persistir_xml_rascunho_nfce(
            documento=documento
        )
        documento.refresh_from_db()

        self.assertEqual(
            documento.status,
            StatusDocumentoFiscal.PREPARADO,
        )
        self.assertTrue(documento.xml_rascunho)
        self.assertIn("<NFe", documento.xml_rascunho)
        self.assertIn("<CRT>3</CRT>", documento.xml_rascunho)
        self.assertIn("qrcode?p=", documento.xml_rascunho.lower())
        mocked.assert_called_once()

    @patch(
        "fiscal.services_assinatura_documento_fiscal."
        "carregar_certificado_a1"
    )
    @patch(
        "fiscal.services_assinatura_documento_fiscal."
        "assinar_xml_nfe"
    )
    @patch(
        "fiscal.services_chave_acesso.secrets.randbelow",
        return_value=12345678,
    )
    def test_persiste_xml_assinado_e_transiciona_status(
        self,
        mocked_rand,
        mocked_assinar,
        mocked_loader,
    ):
        config = ConfiguracaoEmissaoFiscalLoja.objects.get(
            loja=self.loja
        )
        config.certificado_a1_referencia = "certificados/teste.pfx"
        config.save(
            update_fields=(
                "certificado_a1_referencia",
                "atualizado_em",
            )
        )

        documento, _, _ = preparar_documento_fiscal(
            venda_fiscal=self.venda_fiscal,
            modelo=ModeloDocumentoFiscal.NFCE,
            ambiente=AmbienteDocumentoFiscal.HOMOLOGACAO,
            serie=1,
        )
        documento = gerar_e_persistir_xml_rascunho_nfce(
            documento=documento
        )

        mocked_loader.return_value = object()
        mocked_assinar.return_value = "<NFe>assinado</NFe>"

        documento = assinar_documento_fiscal(
            documento=documento,
            senha_certificado="senha-so-teste",
        )
        documento.refresh_from_db()

        self.assertTrue(documento.xml_rascunho)
        self.assertEqual(
            documento.xml_assinado,
            "<NFe>assinado</NFe>",
        )
        self.assertEqual(
            documento.status,
            StatusDocumentoFiscal.PENDENTE_TRANSMISSAO,
        )
        mocked_loader.assert_called_once()
        mocked_assinar.assert_called_once()
        mocked_rand.assert_called_once()
