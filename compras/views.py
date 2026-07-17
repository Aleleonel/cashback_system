from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.shortcuts import redirect, render

from .choices import StatusFornecedor
from .forms import FornecedorForm
from .selectors import (
    get_fornecedor_por_uuid,
    get_fornecedores,
)
from .services import (
    criar_fornecedor,
    editar_fornecedor,
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