from django.contrib.auth import get_user_model
from django.db import transaction

from auditoria.models import RegistroAuditoria
from auditoria.services import registrar_auditoria
from core.choices import StatusOperacional
from core.services import garantir_configuracao_sistema
from empresas.models import Loja, Matriz


def implantar_empresa(
    *,
    dados_matriz,
    dados_loja,
    dados_admin,
    usuario_executor,
    request=None
):

    User = get_user_model()

    with transaction.atomic():

        matriz = Matriz.objects.create(
            nome=dados_matriz['nome'],
            cnpj=dados_matriz.get('cnpj') or None,
            status=StatusOperacional.ATIVA
        )

        loja = Loja.objects.create(
            matriz=matriz,
            nome=dados_loja['nome'],
            cnpj=dados_loja.get('cnpj') or None,
            telefone=dados_loja.get('telefone') or None,
            status=StatusOperacional.ATIVA
        )

        usuario_admin = User.objects.create_user(
            username=dados_admin['username'],
            email=dados_admin.get('email') or '',
            password=dados_admin['password'],
            first_name=dados_admin.get('first_name') or '',
            matriz=matriz,
            perfil=User.PERFIL_MASTER,
            ativo=True,
        )

        usuario_admin.lojas.add(loja)

        garantir_configuracao_sistema(
            matriz=matriz
        )

        registrar_auditoria(
            usuario=usuario_executor,
            matriz=matriz,
            loja=loja,
            acao=RegistroAuditoria.ACAO_CRIAR,
            recurso='plataforma.implantacao_empresa',
            recurso_id=matriz.id,
            descricao=(
                f'Empresa implantada. '
                f'Matriz: {matriz.nome}. '
                f'Loja principal: {loja.nome}. '
                f'Administrador: {usuario_admin.username}.'
            ),
            request=request
        )

        return {
            'matriz': matriz,
            'loja': loja,
            'usuario_admin': usuario_admin,
        }
    

def criar_loja_plataforma(
    *,
    dados,
    usuario_executor,
    request=None
):

    loja = Loja.objects.create(
        matriz=dados['matriz'],
        nome=dados['nome'],
        cnpj=dados.get('cnpj') or None,
        telefone=dados.get('telefone') or None,
        status=dados['status']
    )

    registrar_auditoria(
        usuario=usuario_executor,
        matriz=loja.matriz,
        loja=loja,
        acao=RegistroAuditoria.ACAO_CRIAR,
        recurso='plataforma.loja',
        recurso_id=loja.id,
        descricao=f'Loja criada: {loja.nome}',
        request=request
    )

    return loja


def editar_loja_plataforma(
    *,
    loja,
    dados,
    usuario_executor,
    request=None
):

    loja.matriz = dados['matriz']
    loja.nome = dados['nome']
    loja.cnpj = dados.get('cnpj') or None
    loja.telefone = dados.get('telefone') or None
    loja.status = dados['status']

    loja.save(
        update_fields=[
            'matriz',
            'nome',
            'cnpj',
            'telefone',
            'status',
            'atualizada_em',
        ]
    )

    registrar_auditoria(
        usuario=usuario_executor,
        matriz=loja.matriz,
        loja=loja,
        acao=RegistroAuditoria.ACAO_EDITAR,
        recurso='plataforma.loja',
        recurso_id=loja.id,
        descricao=f'Loja editada: {loja.nome}',
        request=request
    )

    return loja


def alternar_status_loja_plataforma(
    *,
    loja,
    usuario_executor,
    request=None
):

    if loja.status == StatusOperacional.ATIVA:
        loja.status = StatusOperacional.SUSPENSA
        descricao_status = 'suspensa'
    else:
        loja.status = StatusOperacional.ATIVA
        descricao_status = 'ativada'

    loja.save(
        update_fields=[
            'status',
            'atualizada_em',
        ]
    )

    registrar_auditoria(
        usuario=usuario_executor,
        matriz=loja.matriz,
        loja=loja,
        acao=RegistroAuditoria.ACAO_EDITAR,
        recurso='plataforma.loja',
        recurso_id=loja.id,
        descricao=f'Loja {descricao_status}: {loja.nome}',
        request=request
    )

    return loja