from django.core.exceptions import PermissionDenied, ValidationError


def get_contexto_operacional_usuario(usuario):
    if not usuario.is_authenticated:
        raise PermissionDenied('Usuário não autenticado.')

    if not usuario.matriz:
        raise ValidationError('Usuário não está vinculado a uma matriz.')

    lojas = usuario.lojas.filter(ativa=True)

    if not lojas.exists():
        raise ValidationError('Usuário não está vinculado a nenhuma loja ativa.')

    loja = lojas.first()

    return {
        'matriz': usuario.matriz,
        'loja': loja,
    }