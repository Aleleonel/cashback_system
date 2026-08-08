from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from auditoria.models import RegistroAuditoria
from auditoria.services import registrar_auditoria
from fiscal.models_configuracao_fiscal import ConfiguracaoFiscalMatriz


RECURSO_AUDITORIA = "fiscal.configuracao_fiscal_matriz"


def _aplicar_dados(*, configuracao, dados):
    for campo in (
        "regime_tributario",
        "uf_origem",
        "contribuinte_icms",
        "consumidor_final_padrao",
        "ativa",
        "observacoes",
    ):
        if campo in dados:
            setattr(configuracao, campo, dados[campo])

    configuracao.full_clean()
    return configuracao


@transaction.atomic
def criar_configuracao_fiscal_matriz(
    *,
    matriz,
    dados,
    usuario_executor=None,
    loja=None,
    request=None,
):
    if matriz is None:
        raise ValidationError(
            {"matriz": "Informe a matriz da configuracao fiscal."}
        )

    if ConfiguracaoFiscalMatriz.objects.filter(matriz=matriz).exists():
        raise ValidationError(
            {"matriz": "A matriz ja possui uma configuracao fiscal."}
        )

    configuracao = ConfiguracaoFiscalMatriz(matriz=matriz)
    _aplicar_dados(configuracao=configuracao, dados=dados)

    try:
        configuracao.save()
    except IntegrityError as erro:
        raise ValidationError(
            {"matriz": "A matriz ja possui uma configuracao fiscal."}
        ) from erro

    registrar_auditoria(
        usuario=usuario_executor,
        matriz=matriz,
        loja=loja,
        acao=RegistroAuditoria.ACAO_CRIAR,
        recurso=RECURSO_AUDITORIA,
        recurso_id=configuracao.pk,
        descricao="Configuracao fiscal da matriz criada.",
        request=request,
    )
    return configuracao


@transaction.atomic
def atualizar_configuracao_fiscal_matriz(
    *,
    configuracao,
    dados,
    usuario_executor=None,
    loja=None,
    request=None,
):
    if configuracao is None:
        raise ValidationError(
            {"configuracao": "Informe a configuracao fiscal."}
        )

    _aplicar_dados(configuracao=configuracao, dados=dados)
    configuracao.save()

    registrar_auditoria(
        usuario=usuario_executor,
        matriz=configuracao.matriz,
        loja=loja,
        acao=RegistroAuditoria.ACAO_EDITAR,
        recurso=RECURSO_AUDITORIA,
        recurso_id=configuracao.pk,
        descricao="Configuracao fiscal da matriz atualizada.",
        request=request,
    )
    return configuracao
