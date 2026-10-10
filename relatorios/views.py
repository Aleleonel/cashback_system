from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.core.paginator import Paginator
from django.utils import timezone
from empresas.models import Loja

from core.services import get_contexto_operacional_usuario

from .selectors import get_dashboard_resumo, get_relatorio_clientes, get_relatorio_aniversariantes

from accounts.decorators import require_permission
from accounts.permissions import PERMISSAO_RELATORIOS_DASHBOARD


@login_required
@require_permission(PERMISSAO_RELATORIOS_DASHBOARD)
def hub_cadastros(request):
    return render(request, 'relatorios/cadastros.html')

@login_required
@require_permission(PERMISSAO_RELATORIOS_DASHBOARD)
def hub_vendas(request):
    return render(request, 'relatorios/vendas.html')


@login_required
@require_permission(PERMISSAO_RELATORIOS_DASHBOARD)
def hub_financeiro(request):
    return render(request, "relatorios/financeiro.html")


def hub_estoque(request):
    return render(request, 'relatorios/estoque.html')

@login_required
@require_permission(PERMISSAO_RELATORIOS_DASHBOARD)
def dashboard(request):

    contexto = get_contexto_operacional_usuario(
        request.user
    )

    resumo = get_dashboard_resumo(
        matriz=contexto['matriz']
    )

    return render(
        request,
        'relatorios/dashboard.html',
        {
            'resumo': resumo,
        }
    )

@login_required
@require_permission(PERMISSAO_RELATORIOS_DASHBOARD)
def relatorio_clientes(request):
    contexto = get_contexto_operacional_usuario(request.user)
    busca = (request.GET.get('q') or '').strip()
    ativo_raw = (request.GET.get('ativo') or '').strip()
    tipo_pessoa = (request.GET.get('tipo_pessoa') or '').strip()
    loja_raw = (request.GET.get('loja') or '').strip()
    ativo = True if ativo_raw == '1' else False if ativo_raw == '0' else None
    loja_id = int(loja_raw) if loja_raw.isdigit() else None
    clientes_qs = get_relatorio_clientes(
        matriz=contexto['matriz'], ativo=ativo,
        tipo_pessoa=tipo_pessoa or None, loja_id=loja_id, busca=busca or None,
    )
    clientes = Paginator(clientes_qs, 50).get_page(request.GET.get('page'))
    lojas = Loja.objects.filter(matriz=contexto['matriz']).order_by('nome', 'id')
    query_params = request.GET.copy()
    query_params.pop('page', None)
    query_string = query_params.urlencode()
    return render(request, 'relatorios/clientes.html', {
        'clientes': clientes,
        'busca': busca,
        'ativo_filtro': ativo_raw,
        'tipo_pessoa_filtro': tipo_pessoa,
        'loja_filtro': loja_raw,
        'lojas': lojas,
        'query_string': query_string,
    })

@login_required
@require_permission(PERMISSAO_RELATORIOS_DASHBOARD)
def relatorio_aniversariantes(request):
    contexto = get_contexto_operacional_usuario(request.user)
    mes_atual = timezone.localdate().month
    try:
        mes = int(request.GET.get('mes') or mes_atual)
    except (TypeError, ValueError):
        mes = mes_atual
    if mes < 1 or mes > 12:
        mes = mes_atual
    qs = get_relatorio_aniversariantes(matriz=contexto['matriz'], mes=mes)
    paginator = Paginator(qs, 50)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'relatorios/aniversariantes.html', {
        'page_obj': page_obj,
        'mes_filtro': mes,
        'meses': [(i, nome) for i, nome in enumerate(('Janeiro','Fevereiro','Março','Abril','Maio','Junho','Julho','Agosto','Setembro','Outubro','Novembro','Dezembro'), 1)],
    })
