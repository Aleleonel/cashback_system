from configuracoes.decorators import central_configuracoes_required
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import render


from .selectors import get_registros_auditoria
from .models import RegistroAuditoria

@login_required
@central_configuracoes_required
def lista_auditoria(request):
    contexto_acesso = request.contexto_configuracoes
    matriz_auditoria = contexto_acesso.get('matriz')

    acao = request.GET.get('acao', '').strip()
    busca = request.GET.get('q', '').strip()
    data_inicio = request.GET.get('data_inicio', '').strip()
    data_fim = request.GET.get('data_fim', '').strip()

    registros = get_registros_auditoria(
        acao=acao,
        busca=busca,
        data_inicio=data_inicio,
        data_fim=data_fim,
        matriz=matriz_auditoria,
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
            'contexto_auditoria': contexto_acesso,
            'auditoria_plataforma': contexto_acesso.get('escopo') == 'plataforma',
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