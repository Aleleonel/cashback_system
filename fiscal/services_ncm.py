from django.core.exceptions import ValidationError
from django.db import transaction

from auditoria.models import RegistroAuditoria
from auditoria.services import registrar_auditoria
from fiscal.models import NCM


def _validar(*, codigo, descricao, excluido=None):
    codigo = NCM.normalizar_codigo(codigo)
    descricao = (descricao or "").strip()
    erros = {}

    if len(codigo) != 8:
        erros["codigo"] = "Informe exatamente oito digitos."

    if not descricao:
        erros["descricao"] = "Informe a descricao do NCM."

    duplicados = NCM.objects.filter(codigo=codigo)

    if excluido is not None:
        duplicados = duplicados.exclude(id=excluido.id)

    if codigo and duplicados.exists():
        erros["codigo"] = "Ja existe um NCM com este codigo."

    if erros:
        raise ValidationError(erros)

    return codigo, descricao


def _auditar(
    *,
    ncm,
    usuario,
    matriz,
    loja,
    request,
    acao,
    descricao,
):
    registrar_auditoria(
        usuario=usuario,
        matriz=matriz,
        loja=loja,
        acao=acao,
        recurso="fiscal.ncm",
        recurso_id=ncm.id,
        descricao=descricao,
        request=request,
    )


@transaction.atomic
def criar_ncm(
    *,
    dados,
    usuario_executor,
    matriz,
    loja=None,
    request=None,
):
    codigo, descricao = _validar(
        codigo=dados.get("codigo"),
        descricao=dados.get("descricao"),
    )

    ncm = NCM(
        codigo=codigo,
        descricao=descricao,
        unidade_tributavel_padrao=(
            dados.get("unidade_tributavel_padrao")
            or ""
        ),
        ativo=dados.get("ativo", True),
    )
    ncm.save()

    _auditar(
        ncm=ncm,
        usuario=usuario_executor,
        matriz=matriz,
        loja=loja,
        request=request,
        acao=RegistroAuditoria.ACAO_CRIAR,
        descricao=f"NCM criado: {ncm}",
    )

    return ncm


@transaction.atomic
def editar_ncm(
    *,
    ncm,
    dados,
    usuario_executor,
    matriz,
    loja=None,
    request=None,
):
    codigo, descricao = _validar(
        codigo=ncm.codigo,
        descricao=dados.get("descricao"),
        excluido=ncm,
    )

    ncm.codigo = codigo
    ncm.descricao = descricao
    ncm.unidade_tributavel_padrao = (
        dados.get("unidade_tributavel_padrao")
        or ""
    )
    ncm.ativo = dados.get("ativo", ncm.ativo)
    ncm.save()

    _auditar(
        ncm=ncm,
        usuario=usuario_executor,
        matriz=matriz,
        loja=loja,
        request=request,
        acao=RegistroAuditoria.ACAO_EDITAR,
        descricao=f"NCM atualizado: {ncm}",
    )

    return ncm
