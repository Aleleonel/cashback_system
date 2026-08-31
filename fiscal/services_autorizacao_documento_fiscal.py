from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils.dateparse import parse_datetime

from fiscal.choices_documento_fiscal import AmbienteDocumentoFiscal, StatusDocumentoFiscal
from fiscal.models_documento_fiscal import DocumentoFiscal
from fiscal.services_autorizacao_xml import (
    interpretar_ret_cons_sit_nfe,
    interpretar_ret_envi_nfe,
    montar_envi_nfe,
    montar_nfe_proc,
)
from fiscal.services_documento_fiscal import transicionar_documento_fiscal


@transaction.atomic
def iniciar_transmissao_documento_fiscal(*, documento):
    documento = DocumentoFiscal.objects.select_for_update().get(pk=documento.pk)
    if documento.status != StatusDocumentoFiscal.PENDENTE_TRANSMISSAO:
        raise ValidationError({"status": "Documento deve estar pendente de transmissao."})
    if not str(documento.xml_assinado or "").strip():
        raise ValidationError({"xml_assinado": "XML assinado ausente para transmissao."})

    transicionar_documento_fiscal(
        documento=documento,
        novo_status=StatusDocumentoFiscal.TRANSMITINDO,
        salvar=True,
    )
    return documento


def preparar_lote_autorizacao(*, documento):
    if documento.status != StatusDocumentoFiscal.TRANSMITINDO:
        raise ValidationError({"status": "Documento deve estar em transmissao."})
    return montar_envi_nfe(
        xml_assinado=documento.xml_assinado,
        id_lote=str(documento.id),
        ind_sinc=1,
    )


@transaction.atomic
def registrar_retorno_autorizacao(*, documento, xml_retorno):
    documento = DocumentoFiscal.objects.select_for_update().get(pk=documento.pk)
    if documento.status != StatusDocumentoFiscal.TRANSMITINDO:
        raise ValidationError({"status": "Retorno exige documento em transmissao."})

    retorno = interpretar_ret_envi_nfe(xml_retorno=xml_retorno)
    documento.xml_retorno = str(xml_retorno or "")
    documento.numero_recibo = retorno.numero_recibo

    if retorno.autorizado:
        if retorno.chave_acesso != documento.chave_acesso:
            raise ValidationError({"chave_acesso": "Chave retornada pela SEFAZ difere do documento."})
        ambiente_esperado = {AmbienteDocumentoFiscal.PRODUCAO: "1", AmbienteDocumentoFiscal.HOMOLOGACAO: "2"}.get(documento.ambiente)
        if ambiente_esperado is None or retorno.ambiente != ambiente_esperado:
            raise ValidationError({"ambiente": "Ambiente retornado pela SEFAZ difere do documento."})
        data_autorizacao = parse_datetime(retorno.data_recebimento)
        if data_autorizacao is None:
            raise ValidationError({"data_autorizacao": "dhRecbto retornado pela SEFAZ e invalido."})
        documento.xml_autorizado = montar_nfe_proc(
            xml_assinado=documento.xml_assinado,
            xml_protocolo=retorno.xml_protocolo,
        )
        documento.save(update_fields=("xml_retorno", "numero_recibo", "xml_autorizado", "atualizado_em"))
        transicionar_documento_fiscal(
            documento=documento,
            novo_status=StatusDocumentoFiscal.AUTORIZADO,
            codigo_status=retorno.codigo_status,
            motivo_status=retorno.motivo_status,
            protocolo_autorizacao=retorno.protocolo,
            data_autorizacao=data_autorizacao,
            salvar=True,
        )
        return documento

    documento.save(update_fields=("xml_retorno", "numero_recibo", "atualizado_em"))
    transicionar_documento_fiscal(
        documento=documento,
        novo_status=StatusDocumentoFiscal.REJEITADO,
        codigo_status=retorno.codigo_status,
        motivo_status=retorno.motivo_status,
        salvar=True,
    )
    return documento

@transaction.atomic
def reconciliar_retorno_consulta_protocolo(*, documento, xml_retorno):
    documento = DocumentoFiscal.objects.select_for_update().get(pk=documento.pk)
    if documento.status != StatusDocumentoFiscal.TRANSMITINDO:
        raise ValidationError({"status": "Reconciliacao exige documento em transmissao."})
    retorno = interpretar_ret_cons_sit_nfe(xml_retorno=xml_retorno)
    if not retorno.autorizado:
        return documento
    if retorno.chave_acesso != documento.chave_acesso:
        raise ValidationError({"chave_acesso": "Chave consultada pela SEFAZ difere do documento."})
    ambiente_esperado = {AmbienteDocumentoFiscal.PRODUCAO:"1", AmbienteDocumentoFiscal.HOMOLOGACAO:"2"}.get(documento.ambiente)
    if ambiente_esperado is None or retorno.ambiente != ambiente_esperado:
        raise ValidationError({"ambiente": "Ambiente consultado na SEFAZ difere do documento."})
    data_autorizacao = parse_datetime(retorno.data_recebimento)
    if data_autorizacao is None:
        raise ValidationError({"data_autorizacao": "dhRecbto consultado na SEFAZ e invalido."})
    documento.xml_autorizado = montar_nfe_proc(xml_assinado=documento.xml_assinado, xml_protocolo=retorno.xml_protocolo)
    documento.xml_retorno = str(xml_retorno or "")
    documento.save(update_fields=("xml_retorno","xml_autorizado","atualizado_em"))
    transicionar_documento_fiscal(documento=documento, novo_status=StatusDocumentoFiscal.AUTORIZADO, codigo_status=retorno.codigo_status, motivo_status=retorno.motivo_status, protocolo_autorizacao=retorno.protocolo, data_autorizacao=data_autorizacao, salvar=True)
    return documento
