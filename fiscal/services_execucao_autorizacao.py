from django.db import transaction

from fiscal.models_emissao_fiscal import ConfiguracaoEmissaoFiscalLoja
from fiscal.services_autorizacao_documento_fiscal import (
    iniciar_transmissao_documento_fiscal,
    preparar_lote_autorizacao,
    registrar_retorno_autorizacao,
)
from fiscal.services_certificado_a1 import carregar_certificado_a1
from fiscal.services_transporte_sefaz import transmitir_autorizacao_nfce_sp


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
    senha_certificado_a1: str,
    timeout: float = 30.0,
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