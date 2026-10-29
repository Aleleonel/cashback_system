from django.shortcuts import render

from configuracoes.decorators import central_configuracoes_required


@central_configuracoes_required
def vouchers(request):
    return render(
        request,
        "configuracoes/vouchers.html",
        {"contexto_configuracoes": request.contexto_configuracoes},
    )
