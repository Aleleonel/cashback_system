from fiscal.services_autorizacao_documento_fiscal import iniciar_transmissao_documento_fiscal
from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.db import transaction

from fiscal.choices_documento_fiscal import (
    AmbienteDocumentoFiscal,
    ModeloDocumentoFiscal,
    StatusDocumentoFiscal,
)
from fiscal.services_assinatura_documento_fiscal import assinar_documento_fiscal
from fiscal.services_execucao_autorizacao import (
    ExecucaoAutorizacaoError,
    executar_autorizacao_nfce_sp,
    executar_consulta_protocolo_nfce_sp,
)
from fiscal.services_geracao_xml_documento_fiscal import (
    gerar_e_persistir_xml_rascunho_nfce,
)
from fiscal.services_preparacao_documento_fiscal import preparar_documento_fiscal
from fiscal.tests.test_integracao_persistencia_xml_nfce import (
    IntegracaoPersistenciaXMLNFCeTests,
)


class ExecucaoAutorizacaoTests(IntegracaoPersistenciaXMLNFCeTests.__bases__[0]):
    def _documento_assinado(self):
        config = self._configuracao_emissao()
        config.certificado_a1_referencia = "certificados/teste.pfx"
        config.save(
            update_fields=(
                "certificado_a1_referencia",
                "atualizado_em",
            )
        )

        documento, _dados, _criado = preparar_documento_fiscal(
            venda_fiscal=self.venda_fiscal,
            modelo=ModeloDocumentoFiscal.NFCE,
            ambiente=AmbienteDocumentoFiscal.HOMOLOGACAO,
            serie=1,
        )
        documento = gerar_e_persistir_xml_rascunho_nfce(documento=documento)
        with (
            patch(
                "fiscal.services_assinatura_documento_fiscal.carregar_certificado_a1",
                return_value=SimpleNamespace(),
            ),
            patch(
                "fiscal.services_assinatura_documento_fiscal.assinar_xml_nfe",
                side_effect=lambda *, xml, certificado_a1: xml,
            ),
        ):
            documento = assinar_documento_fiscal(
                documento=documento,
                resolvedor_senha=lambda referencia: "segredo-teste",
            )
        documento.refresh_from_db()
        self.assertEqual(StatusDocumentoFiscal.PENDENTE_TRANSMISSAO, documento.status)
        return documento

    def setUp(self):
        IntegracaoPersistenciaXMLNFCeTests.setUp(self)

    def _configuracao_emissao(self):
        from fiscal.models_emissao_fiscal import ConfiguracaoEmissaoFiscalLoja
        return ConfiguracaoEmissaoFiscalLoja.objects.get(loja=self.loja)

    def _configurar_a1(self):
        config = self._configuracao_emissao()
        config.certificado_a1_referencia = "teste-a1.pfx"
        config.save(update_fields=["certificado_a1_referencia"])
        return config

    def test_execucao_autorizada_mockada(self):
        documento = self._documento_assinado()
        config = self._configurar_a1()
        certificado = SimpleNamespace()
        carregador = Mock(return_value=certificado)
        chave = documento.chave_acesso
        retorno = (
            '<retEnviNFe xmlns="http://www.portalfiscal.inf.br/nfe" versao="4.00">'
            '<tpAmb>2</tpAmb><verAplic>TESTE</verAplic>'
            '<cStat>104</cStat><xMotivo>Lote processado</xMotivo>'
            '<protNFe versao="4.00"><infProt>'
            '<tpAmb>2</tpAmb><verAplic>TESTE</verAplic>'
            f'<chNFe>{chave}</chNFe>'
            '<dhRecbto>2026-08-30T13:00:00-03:00</dhRecbto>'
            '<nProt>135260000000001</nProt><digVal>AA==</digVal>'
            '<cStat>100</cStat><xMotivo>Autorizado o uso da NF-e</xMotivo>'
            '</infProt></protNFe></retEnviNFe>'
        )
        observado = {}
        def transmissor(**kwargs):
            documento.refresh_from_db()
            observado["status"] = documento.status
            connection = transaction.get_connection()
            observado["atomic_blocks"] = [
                getattr(block, "_from_testcase", False)
                for block in getattr(connection, "atomic_blocks", [])
            ]
            observado["ambiente"] = kwargs["ambiente"]
            observado["timeout"] = kwargs["timeout"]
            return SimpleNamespace(xml_retorno=retorno, http_status=200)

        resultado = executar_autorizacao_nfce_sp(
            documento=documento,
            resolvedor_senha=lambda referencia: "senha-nao-persistir",
            timeout=9.0,
            carregador_certificado=carregador,
            transmissor=transmissor,
        )
        resultado.refresh_from_db()
        self.assertEqual(StatusDocumentoFiscal.AUTORIZADO, resultado.status)
        self.assertTrue(resultado.xml_autorizado)
        self.assertEqual(StatusDocumentoFiscal.TRANSMITINDO, observado["status"])
        self.assertTrue(observado["atomic_blocks"])
        self.assertTrue(all(observado["atomic_blocks"]))
        self.assertEqual(config.ambiente_nfce, observado["ambiente"])
        self.assertEqual(9.0, observado["timeout"])
        carregador.assert_called_once_with(
            referencia="teste-a1.pfx",
            senha="senha-nao-persistir",
        )

    def test_falha_local_preflight_nao_consume_tentativa(self):
        documento = self._documento_assinado()
        self._configurar_a1()
        tentativa = documento.tentativa_atual
        transmissor = Mock()
        def falhar_certificado(**kwargs):
            raise RuntimeError("falha-local-a1")
        with self.assertRaisesRegex(RuntimeError, "falha-local-a1"):
            executar_autorizacao_nfce_sp(
                documento=documento,
                resolvedor_senha=lambda referencia: "x",
                carregador_certificado=falhar_certificado,
                transmissor=transmissor,
            )
        documento.refresh_from_db()
        self.assertEqual(StatusDocumentoFiscal.PENDENTE_TRANSMISSAO, documento.status)
        self.assertEqual(tentativa, documento.tentativa_atual)
        transmissor.assert_not_called()

    def test_configuracao_invalida_nao_consume_tentativa(self):
        documento = self._documento_assinado()
        tentativa = documento.tentativa_atual
        config = self._configuracao_emissao()
        config.certificado_a1_referencia = ""
        config.save(update_fields=["certificado_a1_referencia"])
        with self.assertRaisesRegex(
            ExecucaoAutorizacaoError,
            "Referencia do certificado A1 nao configurada",
        ):
            executar_autorizacao_nfce_sp(
                documento=documento,
                resolvedor_senha=lambda referencia: "x",
                carregador_certificado=Mock(),
                transmissor=Mock(),
            )
        documento.refresh_from_db()
        self.assertEqual(StatusDocumentoFiscal.PENDENTE_TRANSMISSAO, documento.status)
        self.assertEqual(tentativa, documento.tentativa_atual)

    def test_falha_transporte_mantem_transmitindo_sem_atomic(self):
        documento = self._documento_assinado()
        self._configurar_a1()
        observado = {}
        def transmissor(**kwargs):
            documento.refresh_from_db()
            observado["status"] = documento.status
            connection = transaction.get_connection()
            observado["atomic_blocks"] = [
                getattr(block, "_from_testcase", False)
                for block in getattr(connection, "atomic_blocks", [])
            ]
            raise RuntimeError("timeout-sintetico")
        with self.assertRaisesRegex(RuntimeError, "timeout-sintetico"):
            executar_autorizacao_nfce_sp(
                documento=documento,
                resolvedor_senha=lambda referencia: "x",
                carregador_certificado=Mock(return_value=SimpleNamespace()),
                transmissor=transmissor,
            )
        documento.refresh_from_db()
        self.assertEqual(StatusDocumentoFiscal.TRANSMITINDO, documento.status)
        self.assertEqual(StatusDocumentoFiscal.TRANSMITINDO, observado["status"])
        self.assertTrue(observado["atomic_blocks"])
        self.assertTrue(all(observado["atomic_blocks"]))
        self.assertEqual(1, documento.tentativa_atual)

    def test_atomic_explicito_da_aplicacao_bloqueia_antes_da_tentativa(self):
        documento = self._documento_assinado()
        self._configurar_a1()
        tentativa = documento.tentativa_atual
        transmissor = Mock()

        with transaction.atomic():
            with self.assertRaisesRegex(
                ExecucaoAutorizacaoError,
                "Transporte SEFAZ nao pode ocorrer dentro de transaction.atomic",
            ):
                executar_autorizacao_nfce_sp(
                    documento=documento,
                    resolvedor_senha=lambda referencia: "x",
                    carregador_certificado=Mock(return_value=SimpleNamespace()),
                    transmissor=transmissor,
                )

        documento.refresh_from_db()
        self.assertEqual(
            StatusDocumentoFiscal.PENDENTE_TRANSMISSAO,
            documento.status,
        )
        self.assertEqual(tentativa, documento.tentativa_atual)
        transmissor.assert_not_called()

    def test_senha_a1_nao_e_campo_persistido(self):
        config = self._configuracao_emissao()
        nomes = {field.name for field in config._meta.fields}
        self.assertNotIn("senha_certificado_a1", nomes)
        self.assertNotIn("senha_certificado", nomes)
        self.assertNotIn("senha_a1", nomes)
    def _retorno_consulta_execucao(self, documento, cstat='100', motivo='Autorizado o uso da NF-e'):
        if cstat == '100':
            return (
                '<retConsSitNFe xmlns="http://www.portalfiscal.inf.br/nfe" versao="4.00">'
                '<tpAmb>2</tpAmb><verAplic>TESTE</verAplic><cStat>100</cStat><xMotivo>Autorizado</xMotivo>'
                f'<chNFe>{documento.chave_acesso}</chNFe>'
                '<protNFe versao="4.00"><infProt><tpAmb>2</tpAmb><verAplic>TESTE</verAplic>'
                f'<chNFe>{documento.chave_acesso}</chNFe>'
                '<dhRecbto>2026-08-31T13:00:00-03:00</dhRecbto><nProt>135260000000002</nProt>'
                '<cStat>100</cStat><xMotivo>Autorizado o uso da NF-e</xMotivo></infProt></protNFe>'
                '</retConsSitNFe>'
            )
        return (
            '<retConsSitNFe xmlns="http://www.portalfiscal.inf.br/nfe" versao="4.00">'
            '<tpAmb>2</tpAmb><verAplic>TESTE</verAplic>'
            f'<cStat>{cstat}</cStat><xMotivo>{motivo}</xMotivo>'
            f'<chNFe>{documento.chave_acesso}</chNFe></retConsSitNFe>'
        )

    def test_consulta_protocolo_autorizada_mockada(self):
        documento = self._documento_assinado()
        self._configurar_a1()
        documento = iniciar_transmissao_documento_fiscal(documento=documento)
        tentativa = documento.tentativa_atual
        certificado = SimpleNamespace()
        carregador = Mock(return_value=certificado)
        observado = {}
        def transmissor(**kwargs):
            documento.refresh_from_db()
            observado['status'] = documento.status
            observado['tentativa'] = documento.tentativa_atual
            connection = transaction.get_connection()
            observado['atomic_blocks'] = [getattr(block, '_from_testcase', False) for block in getattr(connection, 'atomic_blocks', [])]
            observado.update(kwargs)
            return SimpleNamespace(xml_retorno=self._retorno_consulta_execucao(documento), http_status=200)
        resultado = executar_consulta_protocolo_nfce_sp(documento=documento, resolvedor_senha=lambda referencia: 'senha-consulta', timeout=11.0, carregador_certificado=carregador, transmissor=transmissor)
        resultado.refresh_from_db()
        self.assertEqual(StatusDocumentoFiscal.AUTORIZADO, resultado.status)
        self.assertEqual(tentativa, resultado.tentativa_atual)
        self.assertEqual(StatusDocumentoFiscal.TRANSMITINDO, observado['status'])
        self.assertEqual(tentativa, observado['tentativa'])
        self.assertTrue(observado['atomic_blocks'])
        self.assertTrue(all(observado['atomic_blocks']))
        self.assertEqual(documento.chave_acesso, observado['chave_acesso'])
        self.assertEqual('homologacao', observado['ambiente'])
        self.assertEqual(certificado, observado['certificado_a1'])
        self.assertEqual(11.0, observado['timeout'])
        self.assertEqual('135260000000002', resultado.protocolo_autorizacao)
        self.assertIn('<nfeProc', resultado.xml_autorizado)
        carregador.assert_called_once_with(referencia='teste-a1.pfx', senha='senha-consulta')

    def test_consulta_protocolo_217_nao_incrementa(self):
        documento = self._documento_assinado()
        self._configurar_a1()
        documento = iniciar_transmissao_documento_fiscal(documento=documento)
        tentativa = documento.tentativa_atual
        transmissor = Mock(return_value=SimpleNamespace(xml_retorno=self._retorno_consulta_execucao(documento, cstat='217', motivo='NF-e nao consta'), http_status=200))
        resultado = executar_consulta_protocolo_nfce_sp(documento=documento, resolvedor_senha=lambda referencia: 'senha-consulta', carregador_certificado=Mock(return_value=SimpleNamespace()), transmissor=transmissor)
        resultado.refresh_from_db()
        self.assertEqual(StatusDocumentoFiscal.TRANSMITINDO, resultado.status)
        self.assertEqual(tentativa, resultado.tentativa_atual)
        self.assertEqual('', resultado.xml_autorizado)
        transmissor.assert_called_once()

    def test_consulta_protocolo_exige_transmitindo_antes_da_rede(self):
        documento = self._documento_assinado()
        self._configurar_a1()
        transmissor = Mock()
        carregador = Mock(return_value=SimpleNamespace())
        with self.assertRaisesRegex(ExecucaoAutorizacaoError, 'exige documento em transmissao'):
            executar_consulta_protocolo_nfce_sp(documento=documento, resolvedor_senha=lambda referencia: 'x', carregador_certificado=carregador, transmissor=transmissor)
        documento.refresh_from_db()
        self.assertEqual(StatusDocumentoFiscal.PENDENTE_TRANSMISSAO, documento.status)
        self.assertEqual(0, documento.tentativa_atual)
        transmissor.assert_not_called()
        carregador.assert_not_called()

    def test_consulta_protocolo_atomic_explicito_bloqueia_rede(self):
        documento = self._documento_assinado()
        self._configurar_a1()
        documento = iniciar_transmissao_documento_fiscal(documento=documento)
        tentativa = documento.tentativa_atual
        transmissor = Mock()
        with transaction.atomic():
            with self.assertRaisesRegex(ExecucaoAutorizacaoError, 'Transporte SEFAZ nao pode ocorrer dentro de transaction.atomic'):
                executar_consulta_protocolo_nfce_sp(documento=documento, resolvedor_senha=lambda referencia: 'x', carregador_certificado=Mock(return_value=SimpleNamespace()), transmissor=transmissor)
        documento.refresh_from_db()
        self.assertEqual(StatusDocumentoFiscal.TRANSMITINDO, documento.status)
        self.assertEqual(tentativa, documento.tentativa_atual)
        transmissor.assert_not_called()
