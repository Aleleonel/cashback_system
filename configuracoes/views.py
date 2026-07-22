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

@central_configuracoes_required
def empresa(request):
    contexto_acesso = request.contexto_configuracoes

    return render(
        request,
        "configuracoes/empresa.html",
        {
            "contexto_configuracoes": contexto_acesso,
            "pode_operar_empresa": (
                contexto_acesso["escopo"] == "empresa"
                and contexto_acesso["matriz"] is not None
            ),
        },
    )

