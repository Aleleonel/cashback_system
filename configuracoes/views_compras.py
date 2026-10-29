from django.shortcuts import render

from configuracoes.decorators import central_configuracoes_required


@central_configuracoes_required
def compras(request):
    return render(
        request,
        "configuracoes/compras.html",
        {"contexto_configuracoes": request.contexto_configuracoes},
    )
