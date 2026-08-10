from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone

from fiscal.choices_documento_fiscal import (
    StatusDocumentoFiscal,
)
from fiscal.models_documento_fiscal import (
    SequenciaDocumentoFiscal,
)


TRANSICOES_PERMITIDAS = {
    StatusDocumentoFiscal.RASCUNHO: {
        StatusDocumentoFiscal.PREPARADO,
        StatusDocumentoFiscal.ERRO,
    },
    StatusDocumentoFiscal.PREPARADO: {
        StatusDocumentoFiscal.PENDENTE_TRANSMISSAO,
        StatusDocumentoFiscal.RASCUNHO,
        StatusDocumentoFiscal.ERRO,
    },
    StatusDocumentoFiscal.PENDENTE_TRANSMISSAO: {
        StatusDocumentoFiscal.TRANSMITINDO,
        StatusDocumentoFiscal.ERRO,
    },
    StatusDocumentoFiscal.TRANSMITINDO: {
        StatusDocumentoFiscal.AUTORIZADO,
        StatusDocumentoFiscal.REJEITADO,
        StatusDocumentoFiscal.DENEGADO,
        StatusDocumentoFiscal.CONTINGENCIA,
        StatusDocumentoFiscal.ERRO,
    },
    StatusDocumentoFiscal.REJEITADO: {
        StatusDocumentoFiscal.PREPARADO,
        StatusDocumentoFiscal.ERRO,
    },
    StatusDocumentoFiscal.CONTINGENCIA: {
        StatusDocumentoFiscal.TRANSMITINDO,
        StatusDocumentoFiscal.AUTORIZADO,
        StatusDocumentoFiscal.ERRO,
    },
    StatusDocumentoFiscal.AUTORIZADO: {
        StatusDocumentoFiscal.CANCELADO,
    },
    StatusDocumentoFiscal.DENEGADO: set(),
    StatusDocumentoFiscal.CANCELADO: set(),
    StatusDocumentoFiscal.ERRO: set(),
}


def validar_transicao_documento_fiscal(*, status_atual, novo_status):
    if status_atual == novo_status:
        return

    permitidos = TRANSICOES_PERMITIDAS.get(
        status_atual,
        set(),
    )

    if novo_status not in permitidos:
        raise ValidationError({
            "status": (
                "Transicao de documento fiscal nao permitida: "
                f"{status_atual} -> {novo_status}."
            )
        })


def transicionar_documento_fiscal(
    *,
    documento,
    novo_status,
    codigo_status="",
    motivo_status="",
    protocolo_autorizacao="",
    data_autorizacao=None,
    salvar=True,
):
    validar_transicao_documento_fiscal(
        status_atual=documento.status,
        novo_status=novo_status,
    )

    if documento.status == novo_status:
        return documento

    documento.status = novo_status
    documento.codigo_status = (codigo_status or "").strip()
    documento.motivo_status = (motivo_status or "").strip()

    if protocolo_autorizacao:
        documento.protocolo_autorizacao = (
            protocolo_autorizacao.strip()
        )

    if novo_status == StatusDocumentoFiscal.TRANSMITINDO:
        documento.tentativa_atual += 1
        documento.ultima_tentativa_em = timezone.now()

    if novo_status == StatusDocumentoFiscal.AUTORIZADO:
        if not documento.protocolo_autorizacao:
            raise ValidationError({
                "protocolo_autorizacao": (
                    "Documento autorizado exige protocolo de autorizacao."
                )
            })

        documento.data_autorizacao = (
            data_autorizacao or timezone.now()
        )

    if salvar:
        documento.save()

    return documento


@transaction.atomic
def reservar_proximo_numero_documento_fiscal(
    *,
    matriz,
    loja,
    modelo,
    ambiente,
    serie,
):
    if serie < 1:
        raise ValidationError({
            "serie": "A serie deve ser maior que zero."
        })

    try:
        sequencia, _ = (
            SequenciaDocumentoFiscal.objects
            .select_for_update()
            .get_or_create(
                matriz=matriz,
                loja=loja,
                modelo=modelo,
                ambiente=ambiente,
                serie=serie,
                defaults={
                    "proximo_numero": 1,
                },
            )
        )
    except IntegrityError:
        sequencia = (
            SequenciaDocumentoFiscal.objects
            .select_for_update()
            .get(
                matriz=matriz,
                loja=loja,
                modelo=modelo,
                ambiente=ambiente,
                serie=serie,
            )
        )

    numero = sequencia.proximo_numero
    sequencia.proximo_numero = numero + 1
    sequencia.save(
        update_fields=(
            "proximo_numero",
            "atualizado_em",
        )
    )

    return numero