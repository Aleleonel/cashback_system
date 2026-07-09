from .models import RegistroAuditoria


def get_ip_request(request):
    forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')

    if forwarded_for:
        return forwarded_for.split(',')[0].strip()

    return request.META.get('REMOTE_ADDR')


def registrar_auditoria(
    *,
    usuario=None,
    matriz=None,
    loja=None,
    acao,
    recurso,
    recurso_id=None,
    descricao='',
    request=None
):
    ip = None
    user_agent = ''

    if request:
        ip = get_ip_request(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')

    return RegistroAuditoria.objects.create(
        usuario=usuario if getattr(usuario, 'is_authenticated', False) else None,
        matriz=matriz,
        loja=loja,
        acao=acao,
        recurso=recurso,
        recurso_id=str(recurso_id) if recurso_id else None,
        descricao=descricao,
        ip=ip,
        user_agent=user_agent,
    )