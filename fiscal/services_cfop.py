from django.core.exceptions import ValidationError
from django.db import transaction
from auditoria.models import RegistroAuditoria
from auditoria.services import registrar_auditoria
from fiscal.models import CFOP


def _validar(codigo, descricao, excluido=None):
    codigo = (codigo or "").strip()
    descricao = (descricao or "").strip()
    erros = {}

    try:
        CFOP.classificar_codigo(codigo)
    except ValidationError as erro:
        erros.update(erro.message_dict)

    if not descricao:
        erros["descricao"] = "Informe a descricao do CFOP."

    duplicados = CFOP.objects.filter(codigo=codigo)
    if excluido is not None:
        duplicados = duplicados.exclude(id=excluido.id)
    if codigo and duplicados.exists():
        erros["codigo"] = "Ja existe um CFOP com este codigo."

    if erros:
        raise ValidationError(erros)

    return codigo, descricao


def _auditar(cfop, usuario, matriz, loja, request, acao, descricao):
    registrar_auditoria(
        usuario=usuario,
        matriz=matriz,
        loja=loja,
        acao=acao,
        recurso="fiscal.cfop",
        recurso_id=cfop.id,
        descricao=descricao,
        request=request,
    )


@transaction.atomic
def criar_cfop(*, dados, usuario_executor, matriz, loja=None, request=None):
    codigo, descricao = _validar(dados.get("codigo"), dados.get("descricao"))
    cfop = CFOP(
        codigo=codigo,
        descricao=descricao,
        gera_movimento_estoque=dados.get("gera_movimento_estoque", True),
        permite_devolucao=dados.get("permite_devolucao", False),
        permite_remessa=dados.get("permite_remessa", False),
        ativo=dados.get("ativo", True),
    )
    cfop.save()
    _auditar(
        cfop,
        usuario_executor,
        matriz,
        loja,
        request,
        RegistroAuditoria.ACAO_CRIAR,
        f"CFOP criado: {cfop}",
    )
    return cfop


@transaction.atomic
def editar_cfop(*, cfop, dados, usuario_executor, matriz, loja=None, request=None):
    codigo, descricao = _validar(cfop.codigo, dados.get("descricao"), cfop)
    cfop.codigo = codigo
    cfop.descricao = descricao
    cfop.gera_movimento_estoque = dados.get("gera_movimento_estoque", cfop.gera_movimento_estoque)
    cfop.permite_devolucao = dados.get("permite_devolucao", cfop.permite_devolucao)
    cfop.permite_remessa = dados.get("permite_remessa", cfop.permite_remessa)
    cfop.ativo = dados.get("ativo", cfop.ativo)
    cfop.save()
    _auditar(
        cfop,
        usuario_executor,
        matriz,
        loja,
        request,
        RegistroAuditoria.ACAO_EDITAR,
        f"CFOP atualizado: {cfop}",
    )
    return cfop
