from cashback.models import LancamentoCashback
from clientes.models import Cliente
from empresas.models import Loja
from accounts.models import Usuario
from campanhas.models import CampanhaAniversarioEnvio


def get_resumo_minha_empresa(*, matriz):

    return {
        'total_lojas': Loja.objects.filter(
            matriz=matriz
        ).count(),

        'lojas_ativas': Loja.objects.filter(
            matriz=matriz,
            status='ativa'
        ).count(),

        'usuarios_ativos': Usuario.objects.filter(
            matriz=matriz,
            ativo=True
        ).count(),

        'total_clientes': Cliente.objects.filter(
            matriz=matriz,
            ativo=True
        ).count(),

        'total_lancamentos_cashback': LancamentoCashback.objects.filter(
            matriz=matriz
        ).count(),

        'total_envios_campanhas': CampanhaAniversarioEnvio.objects.filter(
            matriz=matriz
        ).count(),
    }

from django.db.models import Q


def get_lojas_empresa(
    *,
    matriz,
    busca='',
    status=''
):

    lojas = Loja.objects.filter(
        matriz=matriz
    ).order_by(
        'nome'
    )

    if busca:
        lojas = lojas.filter(
            Q(nome__icontains=busca) |
            Q(cnpj__icontains=busca) |
            Q(telefone__icontains=busca)
        )

    if status:
        lojas = lojas.filter(
            status=status
        )

    return lojas

from django.contrib.auth import get_user_model


def get_usuarios_empresa(
    *,
    matriz,
    busca='',
    perfil='',
    status=''
):

    User = get_user_model()

    usuarios = User.objects.filter(
        matriz=matriz
    ).prefetch_related(
        'lojas'
    ).order_by(
        'username'
    )

    if busca:
        usuarios = usuarios.filter(
            Q(username__icontains=busca) |
            Q(first_name__icontains=busca) |
            Q(email__icontains=busca) |
            Q(telefone__icontains=busca)
        )

    if perfil:
        usuarios = usuarios.filter(
            perfil=perfil
        )

    if status == 'ativos':
        usuarios = usuarios.filter(
            ativo=True
        )

    if status == 'inativos':
        usuarios = usuarios.filter(
            ativo=False
        )

    return usuarios