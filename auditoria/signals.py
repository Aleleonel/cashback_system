from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver

from .models import RegistroAuditoria
from .services import registrar_auditoria


def _matriz_do_usuario(user):
    if user is None or getattr(user, "is_superuser", False):
        return None
    return getattr(user, "matriz", None)


@receiver(user_logged_in, dispatch_uid="auditoria.registrar_login")
def registrar_login(sender, request, user, **kwargs):
    registrar_auditoria(
        usuario=user,
        matriz=_matriz_do_usuario(user),
        acao=RegistroAuditoria.ACAO_LOGIN,
        recurso="autenticacao.login",
        descricao="Login realizado.",
        request=request,
    )


@receiver(user_logged_out, dispatch_uid="auditoria.registrar_logout")
def registrar_logout(sender, request, user, **kwargs):
    if user is None:
        return
    registrar_auditoria(
        usuario=user,
        matriz=_matriz_do_usuario(user),
        acao=RegistroAuditoria.ACAO_LOGOUT,
        recurso="autenticacao.logout",
        descricao="Logout realizado.",
        request=request,
    )