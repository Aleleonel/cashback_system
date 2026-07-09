from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import render

from accounts.decorators import require_permission
from accounts.permissions import PERMISSAO_PLATAFORMA_PAINEL_MASTER

from .selectors import get_registros_auditoria
from .models import RegistroAuditoria

@login_required
@require_permission(PERMISSAO_PLATAFORMA_PAINEL_MASTER)
def lista_auditoria(request):

    acao = request.GET.get('acao', '').strip()
    busca = request.GET.get('q', '').strip()
    data_inicio = request.GET.get('data_inicio', '').strip()
    data_fim = request.GET.get('data_fim', '').strip()

    registros = get_registros_auditoria(
        acao=acao,
        busca=busca,
        data_inicio=data_inicio,
        data_fim=data_fim,
    )

    paginator = Paginator(registros, 50)

    page = request.GET.get('page')

    registros = paginator.get_page(page)

    return render(
        request,
        'auditoria/lista_auditoria.html',
        {
            'registros': registros,
            'acao': acao,
            'busca': busca,
            'data_inicio': data_inicio,
            'data_fim': data_fim,
            'acoes': [
                {
                    'valor': valor,
                    'nome': nome,
                    'selecionado': valor == acao,
                }
                for valor, nome in RegistroAuditoria.ACAO_CHOICES
            ],
                    }
    )