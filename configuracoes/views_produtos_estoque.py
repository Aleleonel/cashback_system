from django.shortcuts import render
from configuracoes.decorators import central_configuracoes_required

@central_configuracoes_required
def produtos_estoque(request):
    return render(
        request,
        "configuracoes/produtos_estoque.html",
        {"contexto_configuracoes": request.contexto_configuracoes},
    )