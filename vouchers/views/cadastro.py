from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from accounts.decorators import require_permission
from accounts.permissions import PERMISSAO_VOUCHERS_GERENCIAR
from core.services import get_contexto_operacional_usuario
from vouchers.forms import VoucherForm
from vouchers.models import Voucher
from vouchers.services import criar_voucher, editar_voucher


@login_required
@require_permission(PERMISSAO_VOUCHERS_GERENCIAR)
def criar_voucher_view(request):

    contexto = get_contexto_operacional_usuario(request.user)

    if request.method == 'POST':
        form = VoucherForm(
            request.POST,
            matriz=contexto['matriz']
        )

        if form.is_valid():
            criar_voucher(
                matriz=contexto['matriz'],
                dados=form.cleaned_data,
                usuario_executor=request.user,
                request=request
            )

            messages.success(
                request,
                'Voucher criado com sucesso.'
            )

            return redirect('vouchers:lista_vouchers')

    else:
        form = VoucherForm(
            matriz=contexto['matriz']
        )

    return render(
        request,
        'vouchers/form.html',
        {
            'form': form,
            'titulo': 'Novo Voucher',
        }
    )


@login_required
@require_permission(PERMISSAO_VOUCHERS_GERENCIAR)
def editar_voucher_view(request, voucher_id):

    contexto = get_contexto_operacional_usuario(request.user)

    voucher = get_object_or_404(
        Voucher.objects.prefetch_related(
            'lojas_permitidas'
        ),
        id=voucher_id,
        matriz=contexto['matriz']
    )

    if request.method == 'POST':
        form = VoucherForm(
            request.POST,
            instance=voucher,
            matriz=contexto['matriz']
        )

        if form.is_valid():
            editar_voucher(
                voucher=voucher,
                dados=form.cleaned_data,
                usuario_executor=request.user,
                request=request
            )

            messages.success(
                request,
                'Voucher atualizado com sucesso.'
            )

            return redirect('vouchers:lista_vouchers')

    else:
        form = VoucherForm(
            instance=voucher,
            matriz=contexto['matriz']
        )

    return render(
        request,
        'vouchers/form.html',
        {
            'form': form,
            'titulo': 'Editar Voucher',
            'voucher': voucher,
        }
    )