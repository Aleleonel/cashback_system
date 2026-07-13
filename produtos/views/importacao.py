from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from accounts.decorators import require_permission
from accounts.permissions import (
    PERMISSAO_PRODUTOS_IMPORTAR,
)
from core.services import (
    get_contexto_operacional_usuario,
)
from produtos.forms import ImportarProdutosForm
from produtos.importacao import (
    criar_download_modelo_produtos,
    validar_planilha_produtos,
)


CHAVE_SESSAO_IMPORTACAO = (
    'importacao_produtos_linhas'
)


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
            resultado = validar_planilha_produtos(
                arquivo=form.cleaned_data['arquivo'],
                matriz=contexto['matriz'],
            )

            if not resultado['valido']:
                messages.error(
                    request,
                    resultado['erro_estrutura'],
                )
            else:
                request.session[
                    CHAVE_SESSAO_IMPORTACAO
                ] = resultado['linhas']

                return render(
                    request,
                    (
                        'produtos/importacao/'
                        'confirmar.html'
                    ),
                    {
                        'resultado': resultado,
                        'matriz': contexto['matriz'],
                    },
                )
    else:
        form = ImportarProdutosForm()

    return render(
        request,
        'produtos/importacao/importar.html',
        {
            'form': form,
            'matriz': contexto['matriz'],
        },
    )


@login_required
@require_permission(
    PERMISSAO_PRODUTOS_IMPORTAR
)
def baixar_modelo_importacao_produtos(request):
    return criar_download_modelo_produtos()
