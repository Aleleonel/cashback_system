from django.core.exceptions import ValidationError
from django.db import transaction

from fiscal.choices_documento_fiscal import StatusDocumentoFiscal
from fiscal.models_documento_fiscal import DocumentoFiscal
from fiscal.models_emissao_fiscal import ConfiguracaoEmissaoFiscalLoja
from fiscal.services_assinatura_xml import assinar_xml_nfe
from fiscal.services_certificado_a1 import carregar_certificado_a1
from fiscal.services_documento_fiscal import transicionar_documento_fiscal


@transaction.atomic
def assinar_documento_fiscal(*, documento, senha_certificado):
    """Assina o XML preparado e o deixa pendente para futura transmissao."""
    documento = (
        DocumentoFiscal.objects
        .select_for_update()
        .get(pk=documento.pk)
    )

    if documento.status != StatusDocumentoFiscal.PREPARADO:
        raise ValidationError({
            "status": "Somente DocumentoFiscal PREPARADO pode ser assinado."
        })

    xml_rascunho = str(documento.xml_rascunho or "").strip()
    if not xml_rascunho:
        raise ValidationError({
            "xml_rascunho": "XML rascunho ausente para assinatura."
        })

    try:
        configuracao = ConfiguracaoEmissaoFiscalLoja.objects.get(
            loja_id=documento.loja_id,
            ativa=True,
        )
    except ConfiguracaoEmissaoFiscalLoja.DoesNotExist as exc:
        raise ValidationError({
            "certificado_a1": "Configuracao fiscal ativa da loja nao encontrada."
        }) from exc
    except ConfiguracaoEmissaoFiscalLoja.MultipleObjectsReturned as exc:
        raise ValidationError({
            "certificado_a1": "Existe mais de uma configuracao fiscal ativa para a loja."
        }) from exc

    referencia = str(configuracao.certificado_a1_referencia or "").strip()
    if not referencia:
        raise ValidationError({
            "certificado_a1": "Referencia do certificado A1 nao configurada para a loja."
        })

    certificado_a1 = carregar_certificado_a1(
        referencia=referencia,
        senha=senha_certificado,
    )
    xml_assinado = assinar_xml_nfe(
        xml=xml_rascunho,
        certificado_a1=certificado_a1,
    )

    documento.xml_assinado = xml_assinado
    documento.save(update_fields=("xml_assinado", "atualizado_em"))

    transicionar_documento_fiscal(
        documento=documento,
        novo_status=StatusDocumentoFiscal.PENDENTE_TRANSMISSAO,
        salvar=True,
    )
    return documento