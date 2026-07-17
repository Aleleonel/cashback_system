from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.http import Http404
from django.shortcuts import redirect, render

from .choices import (
    StatusFornecedor,
    StatusPedidoCompra,
)
from .forms import (
    FornecedorForm,
    ItemPedidoCompraForm,
    PedidoCompraForm,
    RecebimentoCompraForm,
)
from .models import ItemPedidoCompra
from .selectors import (
    get_fornecedor_por_uuid,
    get_fornecedores,
    get_pedido_compra_por_uuid,
    get_pedidos_compra,
)
from .services import (
    adicionar_item_pedido_compra,
    cancelar_pedido_compra,
    criar_fornecedor,
    criar_pedido_compra,
    editar_fornecedor,
    editar_pedido_compra,
    enviar_pedido_compra,
    remover_item_pedido_compra,
    receber_pedido_compra,
)


def _get_matriz_usuario(request):
    matriz = getattr(
        request.user,
        'matriz',
        None,
    )

    if matriz is None:
        raise ValidationError(
            'O usuario nao possui matriz vinculada.'
        )

    return matriz


def _aplicar_erros_formulario(
    *,
    form,
    erro,
):
    if hasattr(erro, 'message_dict'):
        for campo, mensagens in erro.message_dict.items():
            destino = (
                campo
                if campo in form.fields
                else None
            )

            for mensagem in mensagens:
                form.add_error(
                    destino,
                    mensagem,
                )
    else:
        form.add_error(
            None,
            erro,
        )


@login_required
def listar_fornecedores(request):
    matriz = _get_matriz_usuario(request)
    busca = request.GET.get('busca', '')
    status = request.GET.get('status', '')

    fornecedores = get_fornecedores(
        matriz=matriz,
        busca=busca,
        status=status,
    )

    pagina = Paginator(
        fornecedores,
        25,
    ).get_page(
        request.GET.get('page')
    )

    return render(
        request,
        'compras/fornecedores/lista.html',
        {
            'pagina': pagina,
            'busca': busca,
            'status': status,
            'status_choices': (
                StatusFornecedor.choices
            ),
        },
    )


@login_required
def criar_fornecedor_view(request):
    matriz = _get_matriz_usuario(request)

    form = FornecedorForm(
        request.POST or None
    )

    if (
        request.method == 'POST'
        and form.is_valid()
    ):
        try:
            fornecedor = criar_fornecedor(
                matriz=matriz,
                dados=form.cleaned_data,
                usuario=request.user,
                request=request,
            )
        except ValidationError as erro:
            _aplicar_erros_formulario(
                form=form,
                erro=erro,
            )
        else:
            messages.success(
                request,
                'Fornecedor cadastrado com sucesso.',
            )

            return redirect(
                'compras:editar_fornecedor',
                fornecedor_uuid=fornecedor.uuid,
            )

    return render(
        request,
        'compras/fornecedores/form.html',
        {
            'form': form,
            'titulo': 'Novo fornecedor',
        },
    )


@login_required
def editar_fornecedor_view(
    request,
    fornecedor_uuid,
):
    matriz = _get_matriz_usuario(request)

    fornecedor = get_fornecedor_por_uuid(
        matriz=matriz,
        fornecedor_uuid=fornecedor_uuid,
    )

    form = FornecedorForm(
        request.POST or None,
        instance=fornecedor,
    )

    if (
        request.method == 'POST'
        and form.is_valid()
    ):
        try:
            fornecedor = editar_fornecedor(
                fornecedor=fornecedor,
                dados=form.cleaned_data,
                usuario=request.user,
                request=request,
            )
        except ValidationError as erro:
            _aplicar_erros_formulario(
                form=form,
                erro=erro,
            )
        else:
            messages.success(
                request,
                'Fornecedor atualizado com sucesso.',
            )

            return redirect(
                'compras:editar_fornecedor',
                fornecedor_uuid=fornecedor.uuid,
            )

    return render(
        request,
        'compras/fornecedores/form.html',
        {
            'form': form,
            'fornecedor': fornecedor,
            'titulo': 'Editar fornecedor',
        },
    )


@login_required
def listar_pedidos_compra(request):
    matriz = _get_matriz_usuario(request)
    busca = request.GET.get('busca', '')
    status = request.GET.get('status', '')

    pedidos = get_pedidos_compra(
        matriz=matriz,
        busca=busca,
        status=status,
    )

    pagina = Paginator(
        pedidos,
        25,
    ).get_page(
        request.GET.get('page')
    )

    return render(
        request,
        'compras/pedidos/lista.html',
        {
            'pagina': pagina,
            'busca': busca,
            'status': status,
            'status_choices': (
                StatusPedidoCompra.choices
            ),
        },
    )


@login_required
def criar_pedido_compra_view(request):
    matriz = _get_matriz_usuario(request)

    form = PedidoCompraForm(
        request.POST or None,
        matriz=matriz,
    )

    if (
        request.method == 'POST'
        and form.is_valid()
    ):
        try:
            pedido = criar_pedido_compra(
                matriz=matriz,
                fornecedor=form.cleaned_data['fornecedor'],
                data_emissao=form.cleaned_data['data_emissao'],
                previsao_entrega=form.cleaned_data[
                    'previsao_entrega'
                ],
                condicao_pagamento=form.cleaned_data[
                    'condicao_pagamento'
                ],
                frete=form.cleaned_data['frete'],
                desconto=form.cleaned_data['desconto'],
                observacoes=form.cleaned_data['observacoes'],
                usuario=request.user,
                request=request,
            )
        except ValidationError as erro:
            _aplicar_erros_formulario(
                form=form,
                erro=erro,
            )
        else:
            messages.success(
                request,
                'Pedido de compra criado com sucesso.',
            )

            return redirect(
                'compras:detalhar_pedido_compra',
                pedido_uuid=pedido.uuid,
            )

    return render(
        request,
        'compras/pedidos/form.html',
        {
            'form': form,
            'titulo': 'Novo pedido de compra',
        },
    )


@login_required
def detalhar_pedido_compra(
    request,
    pedido_uuid,
):
    matriz = _get_matriz_usuario(request)

    pedido = get_pedido_compra_por_uuid(
        matriz=matriz,
        pedido_uuid=pedido_uuid,
    )

    item_form = ItemPedidoCompraForm(
        matriz=matriz,
    )

    return render(
        request,
        'compras/pedidos/detalhe.html',
        {
            'pedido': pedido,
            'item_form': item_form,
        },
    )


@login_required
def editar_pedido_compra_view(
    request,
    pedido_uuid,
):
    matriz = _get_matriz_usuario(request)

    pedido = get_pedido_compra_por_uuid(
        matriz=matriz,
        pedido_uuid=pedido_uuid,
    )

    form = PedidoCompraForm(
        request.POST or None,
        instance=pedido,
        matriz=matriz,
    )

    if (
        request.method == 'POST'
        and form.is_valid()
    ):
        try:
            pedido = editar_pedido_compra(
                pedido=pedido,
                fornecedor=form.cleaned_data['fornecedor'],
                data_emissao=form.cleaned_data['data_emissao'],
                previsao_entrega=form.cleaned_data[
                    'previsao_entrega'
                ],
                condicao_pagamento=form.cleaned_data[
                    'condicao_pagamento'
                ],
                frete=form.cleaned_data['frete'],
                desconto=form.cleaned_data['desconto'],
                observacoes=form.cleaned_data['observacoes'],
                usuario=request.user,
                request=request,
            )
        except ValidationError as erro:
            _aplicar_erros_formulario(
                form=form,
                erro=erro,
            )
        else:
            messages.success(
                request,
                'Pedido de compra atualizado.',
            )

            return redirect(
                'compras:detalhar_pedido_compra',
                pedido_uuid=pedido.uuid,
            )

    return render(
        request,
        'compras/pedidos/form.html',
        {
            'form': form,
            'pedido': pedido,
            'titulo': (
                f'Editar pedido PC-{pedido.numero:06d}'
            ),
        },
    )


@login_required
def adicionar_item_pedido_compra_view(
    request,
    pedido_uuid,
):
    if request.method != 'POST':
        raise Http404

    matriz = _get_matriz_usuario(request)

    pedido = get_pedido_compra_por_uuid(
        matriz=matriz,
        pedido_uuid=pedido_uuid,
    )

    form = ItemPedidoCompraForm(
        request.POST,
        matriz=matriz,
    )

    if form.is_valid():
        try:
            adicionar_item_pedido_compra(
                pedido=pedido,
                produto=form.cleaned_data['produto'],
                quantidade=form.cleaned_data['quantidade'],
                valor_unitario=form.cleaned_data[
                    'valor_unitario'
                ],
                observacoes=form.cleaned_data['observacoes'],
                usuario=request.user,
                request=request,
            )
        except ValidationError as erro:
            _aplicar_erros_formulario(
                form=form,
                erro=erro,
            )
        else:
            messages.success(
                request,
                'Item adicionado ao pedido.',
            )

            return redirect(
                'compras:detalhar_pedido_compra',
                pedido_uuid=pedido.uuid,
            )

    pedido = get_pedido_compra_por_uuid(
        matriz=matriz,
        pedido_uuid=pedido_uuid,
    )

    return render(
        request,
        'compras/pedidos/detalhe.html',
        {
            'pedido': pedido,
            'item_form': form,
        },
    )


@login_required
def remover_item_pedido_compra_view(
    request,
    pedido_uuid,
    item_id,
):
    if request.method != 'POST':
        raise Http404

    matriz = _get_matriz_usuario(request)

    pedido = get_pedido_compra_por_uuid(
        matriz=matriz,
        pedido_uuid=pedido_uuid,
    )

    try:
        item = ItemPedidoCompra.objects.get(
            pk=item_id,
            pedido=pedido,
        )
    except ItemPedidoCompra.DoesNotExist as erro:
        raise Http404 from erro

    try:
        remover_item_pedido_compra(
            item=item,
            usuario=request.user,
            request=request,
        )
    except ValidationError as erro:
        messages.error(
            request,
            '; '.join(erro.messages),
        )
    else:
        messages.success(
            request,
            'Item removido do pedido.',
        )

    return redirect(
        'compras:detalhar_pedido_compra',
        pedido_uuid=pedido.uuid,
    )


@login_required
def enviar_pedido_compra_view(
    request,
    pedido_uuid,
):
    if request.method != 'POST':
        raise Http404

    matriz = _get_matriz_usuario(request)

    pedido = get_pedido_compra_por_uuid(
        matriz=matriz,
        pedido_uuid=pedido_uuid,
    )

    try:
        enviar_pedido_compra(
            pedido=pedido,
            usuario=request.user,
            request=request,
        )
    except ValidationError as erro:
        messages.error(
            request,
            '; '.join(erro.messages),
        )
    else:
        messages.success(
            request,
            'Pedido enviado ao fornecedor.',
        )

    return redirect(
        'compras:detalhar_pedido_compra',
        pedido_uuid=pedido.uuid,
    )


@login_required
def cancelar_pedido_compra_view(
    request,
    pedido_uuid,
):
    if request.method != 'POST':
        raise Http404

    matriz = _get_matriz_usuario(request)

    pedido = get_pedido_compra_por_uuid(
        matriz=matriz,
        pedido_uuid=pedido_uuid,
    )

    try:
        cancelar_pedido_compra(
            pedido=pedido,
            usuario=request.user,
            request=request,
        )
    except ValidationError as erro:
        messages.error(
            request,
            '; '.join(erro.messages),
        )
    else:
        messages.success(
            request,
            'Pedido de compra cancelado.',
        )

    return redirect(
        'compras:detalhar_pedido_compra',
        pedido_uuid=pedido.uuid,
    )

@login_required
def receber_pedido_compra_view(
    request,
    pedido_uuid,
):
    import uuid as uuid_lib

    matriz = _get_matriz_usuario(request)
    pedido = get_pedido_compra_por_uuid(
        matriz=matriz,
        pedido_uuid=pedido_uuid,
    )

    form = RecebimentoCompraForm(
        request.POST or None,
        matriz=matriz,
        pedido=pedido,
        initial={
            'chave_idempotencia': str(
                uuid_lib.uuid4()
            )
        },
    )

    if request.method == 'POST' and form.is_valid():
        try:
            receber_pedido_compra(
                pedido=pedido,
                loja=form.cleaned_data['loja'],
                itens=form.get_itens(),
                chave_idempotencia=(
                    form.cleaned_data[
                        'chave_idempotencia'
                    ]
                ),
                documento_referencia=(
                    form.cleaned_data[
                        'documento_referencia'
                    ]
                ),
                observacoes=(
                    form.cleaned_data['observacoes']
                ),
                usuario=request.user,
                request=request,
            )
        except ValidationError as erro:
            _aplicar_erros_formulario(
                form=form,
                erro=erro,
            )
        else:
            messages.success(
                request,
                'Recebimento registrado com sucesso.',
            )
            return redirect(
                'compras:detalhar_pedido_compra',
                pedido_uuid=pedido.uuid,
            )

    return render(
        request,
        'compras/pedidos/receber.html',
        {
            'pedido': pedido,
            'form': form,
        },
    )
