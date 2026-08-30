from django.core.exceptions import ValidationError
from django.db import transaction

from fiscal.choices_documento_fiscal import ModeloDocumentoFiscal, StatusDocumentoFiscal
from fiscal.models_documento_fiscal import DocumentoFiscal
from fiscal.models_emissao_fiscal import ConfiguracaoEmissaoFiscalLoja
from fiscal.services_preparacao_documento_fiscal import (
    construir_dados_documento_fiscal,
    validar_dados_documento_fiscal,
)
from fiscal.services_xml_nfce import gerar_xml_nfce_195f1c


@transaction.atomic
def gerar_e_persistir_xml_rascunho_nfce(*, documento):
    documento = DocumentoFiscal.objects.select_for_update().get(pk=documento.pk)

    if documento.modelo != ModeloDocumentoFiscal.NFCE:
        raise ValidationError({"modelo": "Geracao XML desta etapa suporta apenas NFC-e."})
    if documento.status != StatusDocumentoFiscal.PREPARADO:
        raise ValidationError({"status": "DocumentoFiscal precisa estar PREPARADO para gerar XML."})
    if documento.xml_rascunho:
        return documento

    configuracao = ConfiguracaoEmissaoFiscalLoja.objects.get(
        loja_id=documento.loja_id,
        ativa=True,
    )

    venda_fiscal = documento.venda_fiscal
    dados = construir_dados_documento_fiscal(
        venda_fiscal=venda_fiscal,
        modelo=documento.modelo,
        ambiente=documento.ambiente,
        serie=documento.serie,
        numero=documento.numero,
    )
    validar_dados_documento_fiscal(dados=dados)

    data_emissao = venda_fiscal.venda.finalizada_em or documento.criado_em
    xml = gerar_xml_nfce_195f1c(
        documento=documento,
        dados=dados,
        data_emissao=data_emissao,
        crt=str(configuracao.crt or "").strip(),
    )
    documento.xml_rascunho = xml
    documento.save(update_fields=("xml_rascunho", "atualizado_em"))
    return documento
