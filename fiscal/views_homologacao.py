from django.contrib import messages
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_POST

from accounts.decorators import require_permission
from accounts.permissions import (
    PERMISSAO_PDV_OPERAR,
    PERMISSAO_PDV_VISUALIZAR,
)
from core.choices import StatusOperacional
from core.services import get_contexto_operacional_usuario
from fiscal.choices_documento_fiscal import (
    AmbienteDocumentoFiscal,
    ModeloDocumentoFiscal,
    StatusDocumentoFiscal,
)
from fiscal.models_documento_fiscal import DocumentoFiscal
from fiscal.services_preparacao_documento_fiscal import (
    preparar_documento_fiscal,
)
from pdv.choices import StatusOperacaoVenda, TipoEmissaoVenda
from pdv.models import Venda, VendaFiscal, ItemVendaFiscal


MODELO_HOMOLOGACAO = ModeloDocumentoFiscal.NFCE
AMBIENTE_HOMOLOGACAO = AmbienteDocumentoFiscal.HOMOLOGACAO
SERIE_HOMOLOGACAO = 1


def _venda_do_contexto(request, venda_uuid):
    contexto = get_contexto_operacional_usuario(request.user)
    matriz = contexto["matriz"]
    lojas = request.user.lojas.filter(status=StatusOperacional.ATIVA)

    return get_object_or_404(
        Venda.objects.select_related(
            "matriz",
            "loja",
            "cliente",
            "vendedor",
            "operador",
        ),
        uuid=venda_uuid,
        matriz=matriz,
        loja__in=lojas,
        status__in=(
            StatusOperacaoVenda.FINALIZADA,
            StatusOperacaoVenda.CANCELADA,
        ),
    )


def _snapshot_da_venda(venda):
    return VendaFiscal.objects.filter(venda=venda).first()


def _itens_snapshot(venda):
    return (
        ItemVendaFiscal.objects
        .filter(item_venda__venda=venda)
        .select_related("item_venda", "item_venda__produto")
        .order_by("item_venda__sequencia")
    )


def _documento_homologacao(venda_fiscal):
    if venda_fiscal is None:
        return None

    return (
        DocumentoFiscal.objects
        .filter(
            venda_fiscal=venda_fiscal,
            modelo=MODELO_HOMOLOGACAO,
            ambiente=AMBIENTE_HOMOLOGACAO,
            serie=SERIE_HOMOLOGACAO,
        )
        .order_by("-criado_em", "-id")
        .first()
    )


def _idempotency_key_truncada(documento):
    if documento is None or not documento.idempotency_key:
        return ""

    chave = documento.idempotency_key
    if len(chave) <= 20:
        return chave

    return f"{chave[:16]}...{chave[-4:]}"


def _erros_validacao(exc):
    if hasattr(exc, "message_dict"):
        mensagens = []
        for campo, erros in exc.message_dict.items():
            for erro in erros:
                mensagens.append(f"{campo}: {erro}")
        return " ".join(mensagens)

    if hasattr(exc, "messages"):
        return " ".join(str(item) for item in exc.messages)

    return str(exc)


@require_GET
@require_permission(PERMISSAO_PDV_VISUALIZAR)
def homologacao_documento_fiscal(request, venda_uuid):
    venda = _venda_do_contexto(request, venda_uuid)
    venda_fiscal = _snapshot_da_venda(venda)
    itens_fiscais = _itens_snapshot(venda) if venda_fiscal else []
    documento = _documento_homologacao(venda_fiscal)

    pode_preparar = (
        venda.status == StatusOperacaoVenda.FINALIZADA
        and venda.tipo_emissao == TipoEmissaoVenda.FISCAL
        and venda_fiscal is not None
        and (
            documento is None
            or documento.status in (
                StatusDocumentoFiscal.RASCUNHO,
                StatusDocumentoFiscal.PREPARADO,
            )
        )
    )

    return render(
        request,
        "fiscal/homologacao_documento_fiscal.html",
        {
            "venda": venda,
            "venda_fiscal": venda_fiscal,
            "itens_fiscais": itens_fiscais,
            "documento": documento,
            "idempotency_key_truncada": _idempotency_key_truncada(
                documento
            ),
            "pode_preparar": pode_preparar,
            "modelo_homologacao": MODELO_HOMOLOGACAO,
            "ambiente_homologacao": AMBIENTE_HOMOLOGACAO,
            "serie_homologacao": SERIE_HOMOLOGACAO,
        },
    )


@require_POST
@require_permission(PERMISSAO_PDV_OPERAR)
def preparar_documento_fiscal_homologacao(request, venda_uuid):
    venda = _venda_do_contexto(request, venda_uuid)

    if venda.status != StatusOperacaoVenda.FINALIZADA:
        messages.error(
            request,
            "Somente venda finalizada pode preparar documento fiscal.",
        )
        return redirect(
            "fiscal:homologacao_documento_fiscal",
            venda_uuid=venda.uuid,
        )

    if venda.tipo_emissao != TipoEmissaoVenda.FISCAL:
        messages.error(request, "Venda nao fiscal.")
        return redirect(
            "fiscal:homologacao_documento_fiscal",
            venda_uuid=venda.uuid,
        )

    venda_fiscal = _snapshot_da_venda(venda)
    if venda_fiscal is None:
        messages.error(request, "Snapshot fiscal ausente.")
        return redirect(
            "fiscal:homologacao_documento_fiscal",
            venda_uuid=venda.uuid,
        )

    documento_antes = _documento_homologacao(venda_fiscal)
    ja_preparado = (
        documento_antes is not None
        and documento_antes.status == StatusDocumentoFiscal.PREPARADO
    )

    try:
        documento, _dados, _criado = preparar_documento_fiscal(
            venda_fiscal=venda_fiscal,
            modelo=MODELO_HOMOLOGACAO,
            ambiente=AMBIENTE_HOMOLOGACAO,
            serie=SERIE_HOMOLOGACAO,
        )
    except ValidationError as exc:
        messages.error(request, _erros_validacao(exc))
    else:
        if (
            ja_preparado
            and documento.pk == documento_antes.pk
            and documento.numero == documento_antes.numero
        ):
            messages.info(
                request,
                "Documento fiscal ja estava preparado.",
            )
        else:
            messages.success(
                request,
                "Documento fiscal preparado com sucesso.",
            )

    return redirect(
        "fiscal:homologacao_documento_fiscal",
        venda_uuid=venda.uuid,
    )