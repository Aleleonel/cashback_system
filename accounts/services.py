from django.core.exceptions import PermissionDenied

from .permissions import (
    PERMISSAO_PLATAFORMA_PAINEL_MASTER,
    PERMISSOES_POR_PERFIL,
)


def usuario_tem_permissao(usuario, permissao):
    if not usuario.is_authenticated:
        return False

    if usuario.is_superuser:
        return True

    if permissao == PERMISSAO_PLATAFORMA_PAINEL_MASTER:
        return False

    if not getattr(usuario, 'ativo', False):
        return False

    permissoes = PERMISSOES_POR_PERFIL.get(
        usuario.perfil,
        set()
    )

    return permissao in permissoes


def exigir_permissao(usuario, permissao):
    if not usuario_tem_permissao(usuario, permissao):
        raise PermissionDenied(
            'Você não tem permissão para acessar este recurso.'
        )

from auditoria.models import RegistroAuditoria
from auditoria.services import registrar_auditoria


def criar_usuario_plataforma(
    *,
    dados,
    usuario_executor,
    request=None
):

    from django.contrib.auth import get_user_model

    User = get_user_model()

    usuario = User.objects.create_user(
        username=dados['username'],
        email=dados.get('email') or '',
        password=dados['password'],
        first_name=dados.get('first_name') or '',
        telefone=dados.get('telefone') or None,
        perfil=dados['perfil'],
        matriz=dados['matriz'],
        ativo=dados.get('ativo', True),
    )

    usuario.lojas.set(dados['lojas'])

    registrar_auditoria(
        usuario=usuario_executor,
        matriz=usuario.matriz,
        loja=None,
        acao=RegistroAuditoria.ACAO_CRIAR,
        recurso='accounts.usuario',
        recurso_id=usuario.id,
        descricao=f'Usuário criado: {usuario.username}',
        request=request
    )

    return usuario


def editar_usuario_plataforma(
    *,
    usuario,
    dados,
    usuario_executor,
    request=None
):

    usuario.username = dados['username']
    usuario.email = dados.get('email') or ''
    usuario.first_name = dados.get('first_name') or ''
    usuario.telefone = dados.get('telefone') or None
    usuario.perfil = dados['perfil']
    usuario.matriz = dados['matriz']
    usuario.ativo = dados.get('ativo', False)

    senha = dados.get('password')

    if senha:
        usuario.set_password(senha)

    usuario.save(
        update_fields=[
            'username',
            'email',
            'first_name',
            'telefone',
            'perfil',
            'matriz',
            'ativo',
            'password',
            'atualizado_em',
        ]
    )

    usuario.lojas.set(dados['lojas'])

    registrar_auditoria(
        usuario=usuario_executor,
        matriz=usuario.matriz,
        loja=None,
        acao=RegistroAuditoria.ACAO_EDITAR,
        recurso='accounts.usuario',
        recurso_id=usuario.id,
        descricao=f'Usuário editado: {usuario.username}',
        request=request
    )

    return usuario


def alternar_status_usuario_plataforma(
    *,
    usuario,
    usuario_executor,
    request=None
):

    usuario.ativo = not usuario.ativo

    usuario.save(
        update_fields=[
            'ativo',
            'atualizado_em',
        ]
    )

    status = 'ativado' if usuario.ativo else 'inativado'

    registrar_auditoria(
        usuario=usuario_executor,
        matriz=usuario.matriz,
        loja=None,
        acao=RegistroAuditoria.ACAO_EDITAR,
        recurso='accounts.usuario',
        recurso_id=usuario.id,
        descricao=f'Usuário {status}: {usuario.username}',
        request=request
    )

    return usuario