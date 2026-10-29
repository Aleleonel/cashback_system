from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

from configuracoes.decorators import central_configuracoes_required


@login_required
@central_configuracoes_required
def auditoria_empresa(request):
    """Compatibilidade: a Auditoria canonica vive no app auditoria."""
    return redirect("auditoria:lista_auditoria")