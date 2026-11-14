from django.shortcuts import render


def acesso_restrito_pdv(request, funcionalidade):
    """Apresenta a negativa sem alterar a politica de autorizacao."""
    return render(
        request,
        "pdv/acesso_restrito.html",
        {"funcionalidade_restrita": funcionalidade},
        status=403,
    )
