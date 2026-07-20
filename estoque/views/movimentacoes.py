"""Views relacionadas às movimentações de estoque."""

import uuid

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.shortcuts import redirect, render

from core.services import get_contexto_operacional_usuario
from estoque.choices import OrigemMovimentacao
from estoque.forms import EntradaEstoqueForm
from estoque.selectors import get_movimentacoes
from estoque.services import registrar_entrada_estoque


@login_required
def lista_movimentacoes(request):
    contexto = get_contexto_operacional_usuario(
        request.user
    )

    busca = request.GET.get(
        'busca',
        ''
    ).strip()

    movimentacoes = get_movimentacoes(
        matriz=contexto['matriz'],
        busca=busca,
    )

    paginador = Paginator(
        movimentacoes,
        25
    )

    pagina = paginador.get_page(
        request.GET.get('page')
    )

    return render(
        request,
        'estoque/movimentacoes/lista.html',
        {
            'pagina': pagina,
            'busca': busca,
        }
    )


def _aplicar_erros_entrada(form, erro):
    if hasattr(erro, 'message_dict'):
        for campo, mensagens in erro.message_dict.items():
            destino = campo if campo in form.fields else None
            for mensagem in mensagens:
                form.add_error(destino, mensagem)
        return

    for mensagem in erro.messages:
        form.add_error(None, mensagem)


@login_required
def criar_entrada_estoque(request):
    contexto = get_contexto_operacional_usuario(request.user)
    matriz = contexto['matriz']
    loja_inicial = contexto.get('loja')

    if request.method == 'POST':
        form = EntradaEstoqueForm(
            request.POST,
            matriz=matriz,
            loja_inicial=loja_inicial,
        )

        if form.is_valid():
            dados = form.cleaned_data
            try:
                registrar_entrada_estoque(
                    matriz=matriz,
                    loja=dados['loja'],
                    produto=dados['produto'],
                    tipo=dados['tipo'],
                    origem=OrigemMovimentacao.MANUAL,
                    quantidade=dados['quantidade'],
                    chave_idempotencia=(
                        f'entrada-manual:{matriz.pk}:{uuid.uuid4()}'
                    ),
                    usuario=request.user,
                    observacao=dados['observacao'],
                    documento_referencia=dados['documento_referencia'],
                    origem_id='entrada-manual',
                    request=request,
                )
            except ValidationError as erro:
                _aplicar_erros_entrada(form, erro)
            else:
                messages.success(
                    request,
                    'Entrada de estoque registrada com sucesso.'
                )
                return redirect('estoque:lista_movimentacoes')
    else:
        form = EntradaEstoqueForm(
            matriz=matriz,
            loja_inicial=loja_inicial,
        )

    return render(
        request,
        'estoque/movimentacoes/entrada_form.html',
        {'form': form},
    )

