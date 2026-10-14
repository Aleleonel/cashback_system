from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.core.paginator import Paginator
from django.db.models import Sum
from django.utils import timezone
from empresas.models import Loja
from clientes.models import Cliente
from vouchers.models import Voucher
from vouchers.selectors import get_relatorio_usos_voucher
from cashback.selectors import get_relatorio_movimentacoes_cashback

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


@login_required
@require_permission(PERMISSAO_RELATORIOS_DASHBOARD)
def hub_vouchers(request):
    return render(request, 'relatorios/vouchers.html')


@login_required
@require_permission(PERMISSAO_RELATORIOS_DASHBOARD)
def relatorio_utilizacao_vouchers(request):
    contexto = get_contexto_operacional_usuario(request.user)
    matriz = contexto['matriz']
    perfil = getattr(request.user, 'perfil', None)
    operador = perfil == 'operador'

    if operador:
        lojas_autorizadas = request.user.lojas.filter(matriz=matriz).order_by('nome', 'id')
        loja_id = request.session.get('loja_operacional_id')
        loja = lojas_autorizadas.filter(pk=loja_id).first() if loja_id else None
        if loja is None:
            loja = lojas_autorizadas.first()
            if loja is not None:
                request.session['loja_operacional_id'] = loja.pk
        lojas = lojas_autorizadas.filter(pk=loja.pk) if loja else lojas_autorizadas.none()
    else:
        lojas = Loja.objects.filter(matriz=matriz).order_by('nome', 'id')
        loja_raw = (request.GET.get('loja') or '').strip()
        loja = lojas.filter(pk=loja_raw).first() if loja_raw.isdigit() else None

    data_inicio_raw = (request.GET.get('data_inicio') or '').strip()
    data_fim_raw = (request.GET.get('data_fim') or '').strip()
    voucher_raw = (request.GET.get('voucher') or '').strip()

    from datetime import date
    def parse_data(valor):
        try:
            return date.fromisoformat(valor) if valor else None
        except ValueError:
            return None

    usos = get_relatorio_usos_voucher(
        matriz=matriz,
        loja=loja,
        data_inicio=parse_data(data_inicio_raw),
        data_fim=parse_data(data_fim_raw),
        voucher_id=voucher_raw if voucher_raw.isdigit() else None,
    )
    totais = usos.aggregate(
        valor_compras=Sum('valor_compra'),
        valor_descontos=Sum('valor_desconto'),
    )
    quantidade = usos.count()
    page_obj = Paginator(usos, 50).get_page(request.GET.get('page'))
    vouchers = Voucher.objects.filter(matriz=matriz).order_by('nome', 'id')

    return render(request, 'relatorios/vouchers_utilizacao.html', {
        'page_obj': page_obj,
        'quantidade': quantidade,
        'valor_compras': totais['valor_compras'] or 0,
        'valor_descontos': totais['valor_descontos'] or 0,
        'lojas': lojas,
        'loja_filtro': loja,
        'operador': operador,
        'vouchers': vouchers,
        'voucher_filtro': voucher_raw,
        'data_inicio': data_inicio_raw,
        'data_fim': data_fim_raw,
    })


@login_required
@require_permission(PERMISSAO_RELATORIOS_DASHBOARD)
def hub_cashback(request):
    return render(request, 'relatorios/cashback.html')


@login_required
@require_permission(PERMISSAO_RELATORIOS_DASHBOARD)
def relatorio_movimentacoes_cashback(request):
    contexto = get_contexto_operacional_usuario(request.user)
    matriz = contexto['matriz']
    operador = getattr(request.user, 'perfil', None) == 'operador'

    if operador:
        lojas_autorizadas = request.user.lojas.filter(matriz=matriz).order_by('nome', 'id')
        loja_id = request.session.get('loja_operacional_id')
        loja = lojas_autorizadas.filter(pk=loja_id).first() if loja_id else None
        if loja is None:
            loja = lojas_autorizadas.first()
            if loja is not None:
                request.session['loja_operacional_id'] = loja.pk
        lojas = lojas_autorizadas.filter(pk=loja.pk) if loja else lojas_autorizadas.none()
    else:
        lojas = Loja.objects.filter(matriz=matriz).order_by('nome', 'id')
        loja_raw = (request.GET.get('loja') or '').strip()
        loja = lojas.filter(pk=loja_raw).first() if loja_raw.isdigit() else None

    data_inicio = (request.GET.get('data_inicio') or '').strip()
    data_fim = (request.GET.get('data_fim') or '').strip()
    tipo = (request.GET.get('tipo') or '').strip().upper()
    if tipo not in ('ENTRADA', 'SAIDA'):
        tipo = ''
    cliente_raw = (request.GET.get('cliente') or '').strip()
    cliente_id = int(cliente_raw) if cliente_raw.isdigit() else None

    resultado = get_relatorio_movimentacoes_cashback(
        matriz=matriz,
        loja=loja,
        cliente_id=cliente_id,
        data_inicio=data_inicio or None,
        data_fim=data_fim or None,
        tipo=tipo or None,
    )
    page_obj = Paginator(resultado['movimentacoes'], 50).get_page(request.GET.get('page'))
    clientes = Cliente.objects.filter(matriz=matriz).order_by('nome', 'id')

    return render(request, 'relatorios/cashback_movimentacoes.html', {
        'page_obj': page_obj,
        'quantidade': resultado['quantidade_movimentacoes'],
        'total_gerado': resultado['total_gerado'],
        'total_utilizado': resultado['total_utilizado'],
        'lojas': lojas,
        'loja_filtro': loja,
        'operador': operador,
        'clientes': clientes,
        'cliente_filtro': cliente_raw,
        'tipo_filtro': tipo,
        'data_inicio': data_inicio,
        'data_fim': data_fim,
    })
