from django.contrib.auth import get_user_model
from django.db.models import Q


def get_usuarios_plataforma(
    *,
    busca='',
    perfil='',
    status='',
    matriz_id=''
):

    User = get_user_model()

    usuarios = User.objects.select_related(
        'matriz'
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

    if matriz_id:
        usuarios = usuarios.filter(
            matriz_id=matriz_id
        )

    return usuarios