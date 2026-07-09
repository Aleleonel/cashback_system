from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from accounts.decorators import require_permission
from accounts.permissions import PERMISSAO_VOUCHERS_GERENCIAR
from core.services import get_contexto_operacional_usuario
from vouchers.models import Voucher
from vouchers.selectors import get_vouchers
from vouchers.services import ativar_voucher, inativar_voucher


@login_required
@require_permission(PERMISSAO_VOUCHERS_GERENCIAR)
def lista_vouchers(request):

    contexto = get_contexto_operacional_usuario(request.user)

    busca = request.GET.get('q', '').strip()
    status = request.GET.get('status', '').strip()
    tipo = request.GET.get('tipo', '').strip()
    origem = request.GET.get('origem', '').strip()

    vouchers = get_vouchers(
        matriz=contexto['matriz'],
        busca=busca,
        status=status,
        tipo=tipo,
        origem=origem
    )

    paginator = Paginator(vouchers, 50)
    page = request.GET.get('page')
    vouchers = paginator.get_page(page)

    status_opcoes = [
        {
            'valor': valor,
            'nome': nome,
            'selecionado': status == valor,
        }
        for valor, nome in Voucher.Status.choices
    ]

    tipo_opcoes = [
        {
            'valor': valor,
            'nome': nome,
            'selecionado': tipo == valor,
        }
        for valor, nome in Voucher.Tipo.choices
    ]

    origem_opcoes = [
        {
            'valor': valor,
            'nome': nome,
            'selecionado': origem == valor,
        }
        for valor, nome in Voucher.Origem.choices
    ]

    return render(
        request,
        'vouchers/lista.html',
        {
            'vouchers': vouchers,
            'busca': busca,
            'status': status,
            'tipo': tipo,
            'origem': origem,
            'status_opcoes': status_opcoes,
            'tipo_opcoes': tipo_opcoes,
            'origem_opcoes': origem_opcoes,
        }
    )


@login_required
@require_permission(PERMISSAO_VOUCHERS_GERENCIAR)
def ativar_voucher_view(request, voucher_id):

    contexto = get_contexto_operacional_usuario(request.user)

    voucher = get_object_or_404(
        Voucher,
        id=voucher_id,
        matriz=contexto['matriz']
    )

    ativar_voucher(
        voucher=voucher,
        usuario_executor=request.user,
        request=request
    )

    messages.success(
        request,
        'Voucher ativado com sucesso.'
    )

    return redirect('vouchers:lista_vouchers')


@login_required
@require_permission(PERMISSAO_VOUCHERS_GERENCIAR)
def inativar_voucher_view(request, voucher_id):

    contexto = get_contexto_operacional_usuario(request.user)

    voucher = get_object_or_404(
        Voucher,
        id=voucher_id,
        matriz=contexto['matriz']
    )

    inativar_voucher(
        voucher=voucher,
        usuario_executor=request.user,
        request=request
    )

    messages.success(
        request,
        'Voucher inativado com sucesso.'
    )

    return redirect('vouchers:lista_vouchers')