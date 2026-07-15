from auditoria.models import RegistroAuditoria
from auditoria.services import registrar_auditoria


def auditar_criacao(
    *,
    recurso,
    instancia,
    usuario_executor,
    matriz,
    loja=None,
    descricao='',
    request=None,
):
    return registrar_auditoria(
        usuario=usuario_executor,
        matriz=matriz,
        loja=loja,
        acao=RegistroAuditoria.ACAO_CRIAR,
        recurso=recurso,
        recurso_id=instancia.id,
        descricao=descricao,
        request=request,
    )


def auditar_edicao(
    *,
    recurso,
    instancia,
    usuario_executor,
    matriz,
    loja=None,
    descricao='',
    request=None,
):
    return registrar_auditoria(
        usuario=usuario_executor,
        matriz=matriz,
        loja=loja,
        acao=RegistroAuditoria.ACAO_EDITAR,
        recurso=recurso,
        recurso_id=instancia.id,
        descricao=descricao,
        request=request,
    )
