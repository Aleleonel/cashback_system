from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import render

from accounts.decorators import require_permission
from accounts.permissions import PERMISSAO_CAMPANHAS_CONFIGURAR
from auditoria.models import RegistroAuditoria
from core.services import get_contexto_operacional_usuario


@login_required
@require_permission(PERMISSAO_CAMPANHAS_CONFIGURAR)
def auditoria_empresa(request):

    contexto = get_contexto_operacional_usuario(request.user)

    busca = request.GET.get('q', '').strip()
    acao = request.GET.get('acao', '').strip()

    registros = RegistroAuditoria.objects.filter(
        matriz=contexto['matriz']
    ).select_related(
        'usuario',
        'matriz',
        'loja',
    ).order_by(
        '-criado_em'
    )

    if busca:
        registros = registros.filter(
            descricao__icontains=busca
        )

    if acao:
        registros = registros.filter(
            acao=acao
        )

    paginator = Paginator(registros, 50)
    page = request.GET.get('page')
    registros = paginator.get_page(page)

    return render(
        request,
        'empresa/auditoria.html',
        {
            'registros': registros,
            'busca': busca,
            'acao': acao,
            'acoes': [
                {
                    'valor': valor,
                    'nome': nome,
                    'selecionado': acao == valor,
                }
                
                for valor, nome in RegistroAuditoria.ACAO_CHOICES
            ],
        }
    )