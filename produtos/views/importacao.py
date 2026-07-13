from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from accounts.decorators import require_permission
from accounts.permissions import PERMISSAO_PRODUTOS_IMPORTAR
from core.services import get_contexto_operacional_usuario
from produtos.forms import ImportarProdutosForm


@login_required
@require_permission(
    PERMISSAO_PRODUTOS_IMPORTAR
)
def importar_produtos_view(request):
    contexto = get_contexto_operacional_usuario(
        request.user
    )

    if request.method == 'POST':
        form = ImportarProdutosForm(
            request.POST,
            request.FILES,
        )

        if form.is_valid():
            messages.info(
                request,
                (
                    'Planilha recebida com sucesso. '
                    'A validação dos produtos será implementada '
                    'na próxima etapa.'
                )
            )
    else:
        form = ImportarProdutosForm()

    return render(
        request,
        'produtos/importacao/importar.html',
        {
            'form': form,
            'matriz': contexto['matriz'],
        }
    )
