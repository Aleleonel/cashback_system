from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.core.exceptions import ValidationError
from django.test import TestCase

from fiscal.choices_documento_fiscal import ModeloDocumentoFiscal, StatusDocumentoFiscal
from fiscal.services_geracao_xml_documento_fiscal import gerar_e_persistir_xml_rascunho_nfce


class GeracaoXMLDocumentoFiscalTests(TestCase):
    def documento(self, **kw):
        base=dict(pk=1, loja_id=1, modelo=ModeloDocumentoFiscal.NFCE, status=StatusDocumentoFiscal.PREPARADO,
                  xml_rascunho="", venda_fiscal=SimpleNamespace(venda=SimpleNamespace(finalizada_em=None)),
                  ambiente="homologacao", serie=1, numero=1, criado_em=object(), save=Mock())
        base.update(kw)
        return SimpleNamespace(**base)


    @patch("fiscal.services_geracao_xml_documento_fiscal.DocumentoFiscal.objects.select_for_update")
    def test_rejeita_status_nao_preparado(self, lock):
        d=self.documento(status=StatusDocumentoFiscal.RASCUNHO)
        lock.return_value.get.return_value=d
        with self.assertRaises(ValidationError):
            gerar_e_persistir_xml_rascunho_nfce(documento=d)


    @patch("fiscal.services_geracao_xml_documento_fiscal.DocumentoFiscal.objects.select_for_update")
    def test_idempotente_se_xml_ja_existe(self, lock):
        d=self.documento(xml_rascunho="<NFe/>")
        lock.return_value.get.return_value=d
        self.assertIs(gerar_e_persistir_xml_rascunho_nfce(documento=d), d)
        d.save.assert_not_called()


    @patch("fiscal.services_geracao_xml_documento_fiscal.ConfiguracaoEmissaoFiscalLoja.objects.get")
    @patch("fiscal.services_geracao_xml_documento_fiscal.gerar_xml_nfce_195f1c", return_value="<NFe/>")
    @patch("fiscal.services_geracao_xml_documento_fiscal.validar_dados_documento_fiscal")
    @patch("fiscal.services_geracao_xml_documento_fiscal.construir_dados_documento_fiscal")
    @patch("fiscal.services_geracao_xml_documento_fiscal.DocumentoFiscal.objects.select_for_update")
    def test_gera_e_persiste(self, lock, construir, validar, gerar, obter_config):
        d=self.documento()
        lock.return_value.get.return_value=d
        obter_config.return_value=SimpleNamespace(crt="3")
        construir.return_value=SimpleNamespace(regime_tributario="normal")
        out=gerar_e_persistir_xml_rascunho_nfce(documento=d)
        self.assertIs(out,d)
        self.assertEqual(d.xml_rascunho,"<NFe/>")
        validar.assert_called_once()
        gerar.assert_called_once()
        self.assertEqual(gerar.call_args.kwargs["crt"], "3")
        d.save.assert_called_once_with(update_fields=("xml_rascunho","atualizado_em"))
