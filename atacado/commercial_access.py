"""Escopo comercial do Atacado. Nao depende da Central de Configuracoes."""
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.db.models import Q
from empresas.models import Loja
from accounts.services import usuario_tem_permissao
from accounts.permissions import PERMISSAO_ATACADO_VISUALIZAR

def exigir_acesso_comercial(request, permissao=PERMISSAO_ATACADO_VISUALIZAR):
    if not usuario_tem_permissao(request.user, permissao):
        raise PermissionDenied("Sem permissao comercial para o Atacado.")
    if request.user.is_superuser:
        valor=(request.GET.get("matriz") or "").strip()
        if not valor.isdecimal():
            raise Http404("Selecione explicitamente uma matriz.")
        from empresas.models import Matriz
        matriz=Matriz.objects.filter(pk=int(valor)).first()
        if matriz is None:
            raise Http404("Matriz invalida.")
        return matriz, Loja.objects.filter(matriz=matriz)
    matriz=getattr(request.user,"matriz",None)
    if matriz is None:
        raise PermissionDenied("Usuario sem matriz.")
    if request.user.perfil == "master":
        return matriz, Loja.objects.filter(matriz=matriz)
    return matriz, request.user.lojas.filter(matriz=matriz)

def filtrar_orcamentos_autorizados(request, queryset, permissao=PERMISSAO_ATACADO_VISUALIZAR):
    matriz, lojas=exigir_acesso_comercial(request, permissao)
    queryset=queryset.filter(matriz=matriz)
    if request.user.is_superuser or request.user.perfil == "master":
        return queryset
    return queryset.filter(loja__in=lojas)
