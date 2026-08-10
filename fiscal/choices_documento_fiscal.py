from django.db import models


class ModeloDocumentoFiscal(models.TextChoices):
    NFE = "55", "NF-e"
    NFCE = "65", "NFC-e"


class AmbienteDocumentoFiscal(models.TextChoices):
    HOMOLOGACAO = "homologacao", "Homologacao"
    PRODUCAO = "producao", "Producao"


class StatusDocumentoFiscal(models.TextChoices):
    RASCUNHO = "rascunho", "Rascunho"
    PREPARADO = "preparado", "Preparado"
    PENDENTE_TRANSMISSAO = (
        "pendente_transmissao",
        "Pendente de transmissao",
    )
    TRANSMITINDO = "transmitindo", "Transmitindo"
    AUTORIZADO = "autorizado", "Autorizado"
    REJEITADO = "rejeitado", "Rejeitado"
    DENEGADO = "denegado", "Denegado"
    CONTINGENCIA = "contingencia", "Contingencia"
    CANCELADO = "cancelado", "Cancelado"
    ERRO = "erro", "Erro"