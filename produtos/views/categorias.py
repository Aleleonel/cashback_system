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
from produtos.forms import CategoriaForm
from produtos.selectors import (
    get_categoria,
    get_categorias,
)
from produtos.services import (
    criar_categoria,
    editar_categoria,
)

from .helpers import (
    aplicar_erros_validacao_no_form,
    obter_por_selector_ou_404,
)


@login_required
@require_permission(
    PERMISSAO_PRODUTOS_GERENCIAR_AUXILIARES
)
def lista_categorias(request):
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

    categorias = get_categorias(
        matriz=contexto['matriz'],
        busca=busca,
        somente_ativas=somente_ativas,
    )

    paginador = Paginator(
        categorias,
        25
    )

    pagina = paginador.get_page(
        request.GET.get('page')
    )

    return render(
        request,
        'produtos/categorias/lista.html',
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
def criar_categoria_view(request):
    contexto = get_contexto_operacional_usuario(
        request.user
    )

    if request.method == 'POST':
        form = CategoriaForm(
            request.POST
        )

        if form.is_valid():
            try:
                criar_categoria(
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
                    'Categoria criada com sucesso.'
                )

                return redirect(
                    'produtos:lista_categorias'
                )
    else:
        form = CategoriaForm()

    return render(
        request,
        'produtos/categorias/form.html',
        {
            'form': form,
            'titulo': 'Nova categoria',
        }
    )


@login_required
@require_permission(
    PERMISSAO_PRODUTOS_GERENCIAR_AUXILIARES
)
def editar_categoria_view(
    request,
    categoria_id,
):
    contexto = get_contexto_operacional_usuario(
        request.user
    )

    categoria = obter_por_selector_ou_404(
        get_categoria,
        matriz=contexto['matriz'],
        categoria_id=categoria_id,
    )

    if request.method == 'POST':
        form = CategoriaForm(
            request.POST,
            instance=categoria,
        )

        if form.is_valid():
            try:
                editar_categoria(
                    categoria=categoria,
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
                    'Categoria atualizada com sucesso.'
                )

                return redirect(
                    'produtos:lista_categorias'
                )
    else:
        form = CategoriaForm(
            instance=categoria
        )

    return render(
        request,
        'produtos/categorias/form.html',
        {
            'form': form,
            'titulo': 'Editar categoria',
            'categoria': categoria,
        }
    )
