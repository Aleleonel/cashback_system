from django.core.exceptions import PermissionDenied, ValidationError

from core.choices import StatusOperacional
from .models import ConfiguracaoSistema


def get_contexto_operacional_usuario(usuario):
    if not usuario.is_authenticated:
        raise PermissionDenied('Usuário não autenticado.')

    if not usuario.matriz:
        raise ValidationError('Usuário não está vinculado a uma matriz.')

    lojas = usuario.lojas.filter(status=StatusOperacional.ATIVA,)

    if not lojas.exists():
        raise ValidationError('Usuário não está vinculado a nenhuma loja ativa.')

    loja = lojas.first()

    return {
        'matriz': usuario.matriz,
        'loja': loja,
    }


def garantir_configuracao_sistema(*, matriz):
    configuracao, criada = ConfiguracaoSistema.objects.get_or_create(
        matriz=matriz,
        defaults={
            'percentual_cashback': 5,
            'dias_liberacao': 7,
            'dias_expiracao': 45,
            'valor_minimo_compra': 0,
            'enviar_email_saldo': True,
            'enviar_email_aniversario': True,
            'enviar_sms_aniversario': False,
        }
    )

    return configuracao

def get_contexto_plataforma(usuario):

    if not usuario.is_authenticated:
        raise PermissionDenied('Usuário não autenticado.')

    if not usuario.is_superuser:
        raise PermissionDenied('Acesso exclusivo da plataforma.')

    return {
        'usuario': usuario,
    }