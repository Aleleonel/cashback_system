from django.db.models import Q
from django.utils import timezone

from .models import AvisoInterno


def _matriz_id_usuario(usuario):
    return getattr(usuario, "matriz_id", None)


def _lojas_ids_usuario(usuario):
    rel = getattr(usuario, "lojas", None)
    if rel is None:
        return []
    try:
        return list(rel.values_list("pk", flat=True))
    except (AttributeError, TypeError):
        return []


def avisos_visiveis_para_usuario(usuario, agora=None):
    """Retorna somente avisos vigentes dentro do escopo do usuario."""
    agora = agora or timezone.now()
    if not getattr(usuario, "is_authenticated", False):
        return AvisoInterno.objects.none()

    # Superuser da plataforma nao pertence obrigatoriamente a matriz.
    # A comunicacao operacional e consumida no contexto de uma matriz;
    # sem matriz, nao inferimos nem misturamos escopos.
    matriz_id = _matriz_id_usuario(usuario)
    if not matriz_id:
        return AvisoInterno.objects.none()

    qs = AvisoInterno.objects.filter(
        matriz_id=matriz_id,
        ativo=True,
        inicio_exibicao__lte=agora,
    ).filter(Q(fim_exibicao__isnull=True) | Q(fim_exibicao__gte=agora))

    lojas_ids = _lojas_ids_usuario(usuario)
    return qs.filter(Q(loja__isnull=True) | Q(loja_id__in=lojas_ids)).distinct()


def aviso_visivel_para_usuario(usuario, pk, agora=None):
    return avisos_visiveis_para_usuario(usuario, agora=agora).filter(pk=pk).first()
