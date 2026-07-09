from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from accounts.decorators import require_permission
from accounts.permissions import PERMISSAO_EMPRESA_CONFIGURAR_CASHBACK
from core.services import (
    garantir_configuracao_sistema,
    get_contexto_operacional_usuario,
)
from empresa.forms import ConfiguracaoCashbackEmpresaForm
from empresa.services import atualizar_configuracao_cashback_empresa


@login_required
@require_permission(PERMISSAO_EMPRESA_CONFIGURAR_CASHBACK)
def configurar_cashback_empresa(request):

    contexto = get_contexto_operacional_usuario(request.user)

    configuracao = garantir_configuracao_sistema(
        matriz=contexto['matriz']
    )

    if request.method == 'POST':
        form = ConfiguracaoCashbackEmpresaForm(
            request.POST,
            instance=configuracao
        )

        if form.is_valid():
            atualizar_configuracao_cashback_empresa(
                configuracao=configuracao,
                dados=form.cleaned_data,
                usuario_executor=request.user,
                request=request
            )

            messages.success(
                request,
                'Configuração de cashback atualizada com sucesso.'
            )

            return redirect('empresa:configurar_cashback')

    else:
        form = ConfiguracaoCashbackEmpresaForm(
            instance=configuracao
        )

    return render(
        request,
        'empresa/configuracao_cashback.html',
        {
            'form': form,
            'configuracao': configuracao,
        }
    )