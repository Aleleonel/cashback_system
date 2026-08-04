from django.core.exceptions import ValidationError
from django.db import transaction

from auditoria.models import RegistroAuditoria
from auditoria.services import registrar_auditoria
from fiscal.models import CEST


def _validar(
    *,
    codigo,
    descricao,
    ncm_referencia="",
    vigencia_inicio=None,
    vigencia_fim=None,
    excluido=None,
):
    codigo = CEST.normalizar_codigo(codigo)
    ncm_referencia = CEST.normalizar_codigo(
        ncm_referencia
    )
    descricao = (descricao or "").strip()
    erros = {}

    if len(codigo) != 7:
        erros["codigo"] = (
            "Informe exatamente sete digitos."
        )

    if not descricao:
        erros["descricao"] = (
            "Informe a descricao do CEST."
        )

    if ncm_referencia and len(ncm_referencia) != 8:
        erros["ncm_referencia"] = (
            "Informe oito digitos para o NCM."
        )

    if (
        vigencia_inicio
        and vigencia_fim
        and vigencia_fim < vigencia_inicio
    ):
        erros["vigencia_fim"] = (
            "O fim da vigencia nao pode ser anterior ao inicio."
        )

    duplicados = CEST.objects.filter(codigo=codigo)
    if excluido is not None:
        duplicados = duplicados.exclude(id=excluido.id)

    if codigo and duplicados.exists():
        erros["codigo"] = (
            "Ja existe um CEST com este codigo."
        )

    if erros:
        raise ValidationError(erros)

    return codigo, descricao, ncm_referencia


def _auditar(
    *,
    cest,
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
        recurso="fiscal.cest",
        recurso_id=cest.id,
        descricao=descricao,
        request=request,
    )


@transaction.atomic
def criar_cest(
    *,
    dados,
    usuario_executor,
    matriz,
    loja=None,
    request=None,
):
    codigo, descricao, ncm_referencia = _validar(
        codigo=dados.get("codigo"),
        descricao=dados.get("descricao"),
        ncm_referencia=dados.get("ncm_referencia"),
        vigencia_inicio=dados.get("vigencia_inicio"),
        vigencia_fim=dados.get("vigencia_fim"),
    )

    cest = CEST(
        codigo=codigo,
        descricao=descricao,
        segmento=(dados.get("segmento") or "").strip(),
        ncm_referencia=ncm_referencia,
        excecao=(dados.get("excecao") or "").strip(),
        versao_tabela=(
            dados.get("versao_tabela") or ""
        ).strip(),
        vigencia_inicio=dados.get("vigencia_inicio"),
        vigencia_fim=dados.get("vigencia_fim"),
        ativo=dados.get("ativo", True),
    )
    cest.save()

    _auditar(
        cest=cest,
        usuario=usuario_executor,
        matriz=matriz,
        loja=loja,
        request=request,
        acao=RegistroAuditoria.ACAO_CRIAR,
        descricao=f"CEST criado: {cest}",
    )
    return cest


@transaction.atomic
def editar_cest(
    *,
    cest,
    dados,
    usuario_executor,
    matriz,
    loja=None,
    request=None,
):
    codigo, descricao, ncm_referencia = _validar(
        codigo=cest.codigo,
        descricao=dados.get("descricao"),
        ncm_referencia=dados.get("ncm_referencia"),
        vigencia_inicio=dados.get("vigencia_inicio"),
        vigencia_fim=dados.get("vigencia_fim"),
        excluido=cest,
    )

    cest.codigo = codigo
    cest.descricao = descricao
    cest.segmento = (
        dados.get("segmento") or ""
    ).strip()
    cest.ncm_referencia = ncm_referencia
    cest.excecao = (
        dados.get("excecao") or ""
    ).strip()
    cest.versao_tabela = (
        dados.get("versao_tabela") or ""
    ).strip()
    cest.vigencia_inicio = dados.get("vigencia_inicio")
    cest.vigencia_fim = dados.get("vigencia_fim")
    cest.ativo = dados.get("ativo", cest.ativo)
    cest.save()

    _auditar(
        cest=cest,
        usuario=usuario_executor,
        matriz=matriz,
        loja=loja,
        request=request,
        acao=RegistroAuditoria.ACAO_EDITAR,
        descricao=f"CEST atualizado: {cest}",
    )
    return cest
