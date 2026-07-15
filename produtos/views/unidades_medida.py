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
from produtos.forms import UnidadeMedidaForm
from produtos.selectors import (
    get_unidade_medida,
    get_unidades_medida,
)
from produtos.services import (
    criar_unidade_medida,
    editar_unidade_medida,
)

from .helpers import (
    aplicar_erros_validacao_no_form,
    obter_por_selector_ou_404,
)


@login_required
@require_permission(
    PERMISSAO_PRODUTOS_GERENCIAR_AUXILIARES
)
def lista_unidades_medida(request):
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

    unidades = get_unidades_medida(
        matriz=contexto['matriz'],
        busca=busca,
        somente_ativas=somente_ativas,
    )

    paginador = Paginator(
        unidades,
        25
    )

    pagina = paginador.get_page(
        request.GET.get('page')
    )

    return render(
        request,
        'produtos/unidades_medida/lista.html',
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
def criar_unidade_medida_view(request):
    contexto = get_contexto_operacional_usuario(
        request.user
    )

    if request.method == 'POST':
        form = UnidadeMedidaForm(
            request.POST
        )

        if form.is_valid():
            try:
                criar_unidade_medida(
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
                    'Unidade de medida criada com sucesso.'
                )

                return redirect(
                    'produtos:lista_unidades_medida'
                )
    else:
        form = UnidadeMedidaForm()

    return render(
        request,
        'produtos/unidades_medida/form.html',
        {
            'form': form,
            'titulo': 'Nova unidade de medida',
        }
    )


@login_required
@require_permission(
    PERMISSAO_PRODUTOS_GERENCIAR_AUXILIARES
)
def editar_unidade_medida_view(
    request,
    unidade_id,
):
    contexto = get_contexto_operacional_usuario(
        request.user
    )

    unidade = obter_por_selector_ou_404(
        get_unidade_medida,
        matriz=contexto['matriz'],
        unidade_id=unidade_id,
    )

    if request.method == 'POST':
        form = UnidadeMedidaForm(
            request.POST,
            instance=unidade,
        )

        if form.is_valid():
            try:
                editar_unidade_medida(
                    unidade=unidade,
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
                    'Unidade de medida atualizada com sucesso.'
                )

                return redirect(
                    'produtos:lista_unidades_medida'
                )
    else:
        form = UnidadeMedidaForm(
            instance=unidade
        )

    return render(
        request,
        'produtos/unidades_medida/form.html',
        {
            'form': form,
            'titulo': 'Editar unidade de medida',
            'unidade': unidade,
        }
    )
