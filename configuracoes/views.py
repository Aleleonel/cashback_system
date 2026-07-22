from django.shortcuts import render

from .catalogo import listar_grupos_configuracao
from .decorators import (
    central_configuracoes_required,
    configuracoes_criticas_required,
)


@central_configuracoes_required
def inicio(request):
    contexto_acesso = request.contexto_configuracoes
    grupos = listar_grupos_configuracao(
        incluir_criticos=contexto_acesso["pode_configuracoes_criticas"]
    )

    return render(
        request,
        "configuracoes/inicio.html",
        {
            "grupos": grupos,
            "contexto_configuracoes": contexto_acesso,
        },
    )


@configuracoes_criticas_required
def criticas(request):
    return render(
        request,
        "configuracoes/criticas.html",
        {
            "contexto_configuracoes": request.contexto_configuracoes,
        },
    )
