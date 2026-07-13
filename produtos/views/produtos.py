from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.shortcuts import redirect, render

from accounts.decorators import require_permission
from accounts.permissions import (
    PERMISSAO_PRODUTOS_CRIAR,
    PERMISSAO_PRODUTOS_EDITAR,
    PERMISSAO_PRODUTOS_VISUALIZAR,
)
from core.services import get_contexto_operacional_usuario
from produtos.choices import StatusProduto
from produtos.forms import ProdutoForm
from produtos.selectors import (
    get_categorias,
    get_marca,
    get_marcas,
    get_produto,
    get_produtos,
)
from produtos.services import (
    criar_produto,
    editar_produto,
)

from .helpers import (
    aplicar_erros_validacao_no_form,
    obter_por_selector_ou_404,
)


def _obter_categoria_filtro(
    *,
    matriz,
    categoria_id,
):
    if not categoria_id:
        return None

    from produtos.selectors import get_categoria

    return obter_por_selector_ou_404(
        get_categoria,
        matriz=matriz,
        categoria_id=categoria_id,
    )


def _obter_marca_filtro(
    *,
    matriz,
    marca_id,
):
    if not marca_id:
        return None

    return obter_por_selector_ou_404(
        get_marca,
        matriz=matriz,
        marca_id=marca_id,
    )


@login_required
@require_permission(
    PERMISSAO_PRODUTOS_VISUALIZAR
)
def lista_produtos(request):
    contexto = get_contexto_operacional_usuario(
        request.user
    )

    matriz = contexto['matriz']

    busca = request.GET.get(
        'busca',
        ''
    ).strip()

    status = request.GET.get(
        'status',
        ''
    ).strip()

    categoria_id = request.GET.get(
        'categoria',
        ''
    ).strip()

    marca_id = request.GET.get(
        'marca',
        ''
    ).strip()

    categoria = _obter_categoria_filtro(
        matriz=matriz,
        categoria_id=categoria_id,
    )

    marca = _obter_marca_filtro(
        matriz=matriz,
        marca_id=marca_id,
    )

    produtos = get_produtos(
        matriz=matriz,
        busca=busca,
        status=status,
        categoria=categoria,
        marca=marca,
    )

    paginador = Paginator(
        produtos,
        25
    )

    pagina = paginador.get_page(
        request.GET.get('page')
    )

    categorias = get_categorias(
        matriz=matriz,
        somente_ativas=True,
    )

    marcas = get_marcas(
        matriz=matriz,
        somente_ativas=True,
    )

    return render(
        request,
        'produtos/produtos/lista.html',
        {
            'pagina': pagina,
            'busca': busca,
            'status': status,
            'categoria_id': categoria_id,
            'marca_id': marca_id,
            'categorias': categorias,
            'marcas': marcas,
            'status_opcoes': StatusProduto.choices,
        }
    )


@login_required
@require_permission(
    PERMISSAO_PRODUTOS_VISUALIZAR
)
def detalhe_produto(
    request,
    produto_id,
):
    contexto = get_contexto_operacional_usuario(
        request.user
    )

    produto = obter_por_selector_ou_404(
        get_produto,
        matriz=contexto['matriz'],
        produto_id=produto_id,
    )

    return render(
        request,
        'produtos/produtos/detalhe.html',
        {
            'produto': produto,
        }
    )


@login_required
@require_permission(
    PERMISSAO_PRODUTOS_CRIAR
)
def criar_produto_view(request):
    contexto = get_contexto_operacional_usuario(
        request.user
    )

    matriz = contexto['matriz']

    if request.method == 'POST':
        form = ProdutoForm(
            request.POST,
            matriz=matriz,
        )

        if form.is_valid():
            try:
                produto = criar_produto(
                    matriz=matriz,
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
                    'Produto criado com sucesso.'
                )

                return redirect(
                    'produtos:detalhe_produto',
                    produto_id=produto.id,
                )
    else:
        form = ProdutoForm(
            matriz=matriz
        )

    return render(
        request,
        'produtos/produtos/form.html',
        {
            'form': form,
            'titulo': 'Novo produto',
            'modo_edicao': False,
        }
    )


@login_required
@require_permission(
    PERMISSAO_PRODUTOS_EDITAR
)
def editar_produto_view(
    request,
    produto_id,
):
    contexto = get_contexto_operacional_usuario(
        request.user
    )

    matriz = contexto['matriz']

    produto = obter_por_selector_ou_404(
        get_produto,
        matriz=matriz,
        produto_id=produto_id,
    )

    if request.method == 'POST':
        form = ProdutoForm(
            request.POST,
            instance=produto,
            matriz=matriz,
        )

        if form.is_valid():
            try:
                produto = editar_produto(
                    produto=produto,
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
                    'Produto atualizado com sucesso.'
                )

                return redirect(
                    'produtos:detalhe_produto',
                    produto_id=produto.id,
                )
    else:
        form = ProdutoForm(
            instance=produto,
            matriz=matriz,
        )

    return render(
        request,
        'produtos/produtos/form.html',
        {
            'form': form,
            'titulo': 'Editar produto',
            'produto': produto,
            'modo_edicao': True,
        }
    )
