from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.shortcuts import redirect, render

from accounts.decorators import require_permission
from accounts.permissions import (
    PERMISSAO_PRODUTOS_GERENCIAR_AUXILIARES,
)
from core.services import get_contexto_operacional_usuario
from produtos.forms import MarcaForm
from produtos.selectors import (
    get_marca,
    get_marcas,
)
from produtos.services import (
    criar_marca,
    editar_marca,
)

from .helpers import (
    aplicar_erros_validacao_no_form,
    obter_por_selector_ou_404,
)


@login_required
@require_permission(
    PERMISSAO_PRODUTOS_GERENCIAR_AUXILIARES
)
def lista_marcas(request):
    contexto = get_contexto_operacional_usuario(
        request.user
    )

    busca = request.GET.get(
        'busca',
        ''
    ).strip()

    somente_ativas = (
        request.GET.get('ativas') == '1'
    )

    marcas = get_marcas(
        matriz=contexto['matriz'],
        busca=busca,
        somente_ativas=somente_ativas,
    )

    paginador = Paginator(
        marcas,
        25
    )

    pagina = paginador.get_page(
        request.GET.get('page')
    )

    return render(
        request,
        'produtos/marcas/lista.html',
        {
            'pagina': pagina,
            'busca': busca,
            'somente_ativas': somente_ativas,
        }
    )


@login_required
@require_permission(
    PERMISSAO_PRODUTOS_GERENCIAR_AUXILIARES
)
def criar_marca_view(request):
    contexto = get_contexto_operacional_usuario(
        request.user
    )

    if request.method == 'POST':
        form = MarcaForm(
            request.POST
        )

        if form.is_valid():
            try:
                criar_marca(
                    matriz=contexto['matriz'],
                    dados=form.cleaned_data,
                    usuario_executor=request.user,
                    loja=contexto.get('loja'),
                    request=request,
                )
            except ValidationError as erro:
                aplicar_erros_validacao_no_form(
                    form=form,
                    erro=erro,
                )
            else:
                messages.success(
                    request,
                    'Marca criada com sucesso.'
                )

                return redirect(
                    'produtos:lista_marcas'
                )
    else:
        form = MarcaForm()

    return render(
        request,
        'produtos/marcas/form.html',
        {
            'form': form,
            'titulo': 'Nova marca',
        }
    )


@login_required
@require_permission(
    PERMISSAO_PRODUTOS_GERENCIAR_AUXILIARES
)
def editar_marca_view(
    request,
    marca_id,
):
    contexto = get_contexto_operacional_usuario(
        request.user
    )

    marca = obter_por_selector_ou_404(
        get_marca,
        matriz=contexto['matriz'],
        marca_id=marca_id,
    )

    if request.method == 'POST':
        form = MarcaForm(
            request.POST,
            instance=marca,
        )

        if form.is_valid():
            try:
                editar_marca(
                    marca=marca,
                    dados=form.cleaned_data,
                    usuario_executor=request.user,
                    loja=contexto.get('loja'),
                    request=request,
                )
            except ValidationError as erro:
                aplicar_erros_validacao_no_form(
                    form=form,
                    erro=erro,
                )
            else:
                messages.success(
                    request,
                    'Marca atualizada com sucesso.'
                )

                return redirect(
                    'produtos:lista_marcas'
                )
    else:
        form = MarcaForm(
            instance=marca
        )

    return render(
        request,
        'produtos/marcas/form.html',
        {
            'form': form,
            'titulo': 'Editar marca',
            'marca': marca,
        }
    )
