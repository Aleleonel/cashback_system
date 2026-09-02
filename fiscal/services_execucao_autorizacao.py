from django.db import transaction

from fiscal.models_emissao_fiscal import ConfiguracaoEmissaoFiscalLoja
from fiscal.services_autorizacao_documento_fiscal import (
    iniciar_transmissao_documento_fiscal,
    preparar_lote_autorizacao,
    reconciliar_retorno_consulta_protocolo,
    registrar_retorno_autorizacao,
)
from fiscal.services_certificado_a1 import carregar_certificado_a1
from fiscal.services_secrets_certificado_a1 import resolver_senha_certificado_a1
from fiscal.choices_documento_fiscal import StatusDocumentoFiscal
from fiscal.services_transporte_sefaz import (
    transmitir_autorizacao_nfce_sp,
    transmitir_consulta_protocolo_nfce_sp,
)


class ExecucaoAutorizacaoError(Exception):
    pass


def _ha_bloco_atomico_de_aplicacao() -> bool:
    conexao = transaction.get_connection()
    return any(
        not getattr(bloco, "_from_testcase", False)
        for bloco in getattr(conexao, "atomic_blocks", ())
    )


def executar_autorizacao_nfce_sp(
    *,
    documento,
    timeout: float = 30.0,
    resolvedor_senha=resolver_senha_certificado_a1,
    carregador_certificado=carregar_certificado_a1,
    transmissor=transmitir_autorizacao_nfce_sp,
):
    try:
        configuracao = ConfiguracaoEmissaoFiscalLoja.objects.get(
            loja=documento.venda_fiscal.venda.loja,
            ativa=True,
        )
    except ConfiguracaoEmissaoFiscalLoja.DoesNotExist as exc:
        raise ExecucaoAutorizacaoError(
            "Configuracao fiscal ativa nao encontrada."
        ) from exc

    if configuracao.uf != "SP":
        raise ExecucaoAutorizacaoError(
            "Autorizacao implementada somente para SP."
        )

    referencia = str(configuracao.certificado_a1_referencia or "").strip()
    if not referencia:
        raise ExecucaoAutorizacaoError(
            "Referencia do certificado A1 nao configurada."
        )

    referencia_segredo = str(
        getattr(configuracao, 'certificado_a1_segredo_referencia', '') or ''
    ).strip()
    senha_certificado_a1 = resolvedor_senha(referencia_segredo)
    certificado_a1 = carregador_certificado(
        referencia=referencia,
        senha=senha_certificado_a1,
    )

    if _ha_bloco_atomico_de_aplicacao():
        raise ExecucaoAutorizacaoError(
            "Transporte SEFAZ nao pode ocorrer dentro de transaction.atomic."
        )

    documento = iniciar_transmissao_documento_fiscal(documento=documento)
    lote = preparar_lote_autorizacao(documento=documento)

    resposta = transmissor(
        xml_envi_nfe=lote,
        ambiente=configuracao.ambiente_nfce,
        certificado_a1=certificado_a1,
        timeout=timeout,
    )

    return registrar_retorno_autorizacao(
        documento=documento,
        xml_retorno=resposta.xml_retorno,
    )


def executar_consulta_protocolo_nfce_sp(
    *,
    documento,
    timeout: float = 30.0,
    resolvedor_senha=resolver_senha_certificado_a1,
    carregador_certificado=carregar_certificado_a1,
    transmissor=transmitir_consulta_protocolo_nfce_sp,
):
    try:
        configuracao = ConfiguracaoEmissaoFiscalLoja.objects.get(
            loja=documento.venda_fiscal.venda.loja,
            ativa=True,
        )
    except ConfiguracaoEmissaoFiscalLoja.DoesNotExist as exc:
        raise ExecucaoAutorizacaoError(
            'Configuracao fiscal ativa nao encontrada.'
        ) from exc

    if configuracao.uf != 'SP':
        raise ExecucaoAutorizacaoError(
            'Consulta de protocolo implementada somente para SP.'
        )

    if documento.status != StatusDocumentoFiscal.TRANSMITINDO:
        raise ExecucaoAutorizacaoError(
            'Consulta de protocolo exige documento em transmissao.'
        )

    chave_acesso = str(documento.chave_acesso or '').strip()
    if len(chave_acesso) != 44 or not chave_acesso.isdigit():
        raise ExecucaoAutorizacaoError(
            'Documento sem chave de acesso valida para consulta.'
        )

    referencia = str(configuracao.certificado_a1_referencia or '').strip()
    if not referencia:
        raise ExecucaoAutorizacaoError(
            'Referencia do certificado A1 nao configurada.'
        )

    referencia_segredo = str(
        getattr(configuracao, 'certificado_a1_segredo_referencia', '') or ''
    ).strip()
    senha_certificado_a1 = resolvedor_senha(referencia_segredo)
    certificado_a1 = carregador_certificado(
        referencia=referencia,
        senha=senha_certificado_a1,
    )

    if _ha_bloco_atomico_de_aplicacao():
        raise ExecucaoAutorizacaoError(
            'Transporte SEFAZ nao pode ocorrer dentro de transaction.atomic.'
        )

    resposta = transmissor(
        chave_acesso=chave_acesso,
        ambiente=configuracao.ambiente_nfce,
        certificado_a1=certificado_a1,
        timeout=timeout,
    )

    return reconciliar_retorno_consulta_protocolo(
        documento=documento,
        xml_retorno=resposta.xml_retorno,
    )
