from django.core.exceptions import PermissionDenied


PERFIS_ADMINISTRATIVOS = {"master", "admin_loja"}


def validar_acesso_central_configuracoes(*, usuario):
    if not getattr(usuario, "is_authenticated", False):
        raise PermissionDenied("Usuário não autenticado.")

    if usuario.is_superuser:
        return {
            "escopo": "plataforma",
            "matriz": None,
            "pode_configuracoes_criticas": True,
        }

    if not getattr(usuario, "ativo", False):
        raise PermissionDenied("Usuário inativo.")

    if getattr(usuario, "perfil", None) not in PERFIS_ADMINISTRATIVOS:
        raise PermissionDenied(
            "A Central de Configurações é exclusiva para administradores."
        )

    matriz = getattr(usuario, "matriz", None)
    if matriz is None:
        raise PermissionDenied("Administrador sem matriz vinculada.")

    return {
        "escopo": "empresa",
        "matriz": matriz,
        "pode_configuracoes_criticas": False,
    }


def validar_acesso_configuracoes_criticas(*, usuario):
    if not getattr(usuario, "is_authenticated", False):
        raise PermissionDenied("Usuário não autenticado.")

    if not usuario.is_superuser:
        raise PermissionDenied(
            "Acesso exclusivo do administrador do sistema."
        )

    return {
        "escopo": "plataforma",
        "matriz": None,
        "pode_configuracoes_criticas": True,
    }
