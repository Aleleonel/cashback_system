"""Views relacionadas às movimentações de estoque."""

import uuid

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.shortcuts import redirect, render

from core.services import get_contexto_operacional_usuario
from estoque.choices import OrigemMovimentacao
from estoque.forms import (
    AjusteEstoqueForm,
    EntradaEstoqueForm,
    SaidaEstoqueForm,
    TransferenciaEstoqueForm,
)
from estoque.selectors import get_movimentacoes
from estoque.services import (
    registrar_ajuste_estoque,
    registrar_entrada_estoque,
    registrar_saida_estoque,
    registrar_transferencia_estoque,
)


@login_required
def lista_movimentacoes(request):
    contexto = get_contexto_operacional_usuario(request.user)

    busca = request.GET.get('busca', '').strip()

    movimentacoes = get_movimentacoes(
        matriz=contexto['matriz'],
        busca=busca,
    )

    paginador = Paginator(movimentacoes, 25)
    pagina = paginador.get_page(request.GET.get('page'))

    return render(
        request,
        'estoque/movimentacoes/lista.html',
        {
            'pagina': pagina,
            'busca': busca,
        }
    )


def _aplicar_erros_servico(form, erro):
    if hasattr(erro, 'message_dict'):
        for campo, mensagens in erro.message_dict.items():
            destino = campo if campo in form.fields else None
            for mensagem in mensagens:
                form.add_error(destino, mensagem)
        return

    for mensagem in erro.messages:
        form.add_error(None, mensagem)


def _render_operacao(request, *, form, titulo, subtitulo, icone, texto_botao):
    return render(
        request,
        'estoque/movimentacoes/operacao_form.html',
        {
            'form': form,
            'titulo': titulo,
            'subtitulo': subtitulo,
            'icone': icone,
            'texto_botao': texto_botao,
        },
    )


@login_required
def criar_entrada_estoque(request):
    contexto = get_contexto_operacional_usuario(request.user)
    matriz = contexto['matriz']
    loja_inicial = contexto.get('loja')

    form = EntradaEstoqueForm(
        request.POST or None,
        matriz=matriz,
        loja_inicial=loja_inicial,
    )

    if request.method == 'POST' and form.is_valid():
        dados = form.cleaned_data
        try:
            registrar_entrada_estoque(
                matriz=matriz,
                loja=dados['loja'],
                produto=dados['produto'],
                tipo=dados['tipo'],
                origem=OrigemMovimentacao.MANUAL,
                quantidade=dados['quantidade'],
                chave_idempotencia=f'entrada-manual:{matriz.pk}:{uuid.uuid4()}',
                usuario=request.user,
                observacao=dados['observacao'],
                documento_referencia=dados['documento_referencia'],
                origem_id='entrada-manual',
                request=request,
            )
        except ValidationError as erro:
            _aplicar_erros_servico(form, erro)
        else:
            messages.success(
                request,
                'Entrada de estoque registrada com sucesso.'
            )
            return redirect('estoque:lista_movimentacoes')

    return _render_operacao(
        request,
        form=form,
        titulo='Nova entrada de estoque',
        subtitulo='Registre a entrada manual de um produto em uma loja.',
        icone='bi-box-arrow-in-down',
        texto_botao='Registrar entrada',
    )


@login_required
def criar_saida_estoque(request):
    contexto = get_contexto_operacional_usuario(request.user)
    matriz = contexto['matriz']
    loja_inicial = contexto.get('loja')

    form = SaidaEstoqueForm(
        request.POST or None,
        matriz=matriz,
        loja_inicial=loja_inicial,
    )

    if request.method == 'POST' and form.is_valid():
        dados = form.cleaned_data
        try:
            registrar_saida_estoque(
                matriz=matriz,
                loja=dados['loja'],
                produto=dados['produto'],
                tipo=dados['tipo'],
                origem=OrigemMovimentacao.MANUAL,
                quantidade=dados['quantidade'],
                chave_idempotencia=f'saida-manual:{matriz.pk}:{uuid.uuid4()}',
                usuario=request.user,
                observacao=dados['observacao'],
                documento_referencia=dados['documento_referencia'],
                origem_id='saida-manual',
                request=request,
            )
        except ValidationError as erro:
            _aplicar_erros_servico(form, erro)
        else:
            messages.success(
                request,
                'Saída de estoque registrada com sucesso.'
            )
            return redirect('estoque:lista_movimentacoes')

    return _render_operacao(
        request,
        form=form,
        titulo='Nova saída de estoque',
        subtitulo='Registre uma saída manual respeitando o saldo disponível.',
        icone='bi-box-arrow-up',
        texto_botao='Registrar saída',
    )


@login_required
def criar_transferencia_estoque(request):
    contexto = get_contexto_operacional_usuario(request.user)
    matriz = contexto['matriz']
    loja_inicial = contexto.get('loja')

    form = TransferenciaEstoqueForm(
        request.POST or None,
        matriz=matriz,
        loja_inicial=loja_inicial,
    )

    if request.method == 'POST' and form.is_valid():
        dados = form.cleaned_data
        try:
            registrar_transferencia_estoque(
                matriz=matriz,
                loja_origem=dados['loja_origem'],
                loja_destino=dados['loja_destino'],
                produto=dados['produto'],
                quantidade=dados['quantidade'],
                chave_idempotencia=f'transferencia:{matriz.pk}:{uuid.uuid4()}',
                motivo=dados['motivo'],
                usuario=request.user,
                documento_referencia=dados['documento_referencia'],
                origem_id='transferencia-manual',
                request=request,
            )
        except ValidationError as erro:
            _aplicar_erros_servico(form, erro)
        else:
            messages.success(
                request,
                'Transferência de estoque registrada com sucesso.'
            )
            return redirect('estoque:lista_movimentacoes')

    return _render_operacao(
        request,
        form=form,
        titulo='Transferência entre lojas',
        subtitulo='Transfira produtos entre lojas da mesma matriz.',
        icone='bi-arrow-left-right',
        texto_botao='Registrar transferência',
    )


@login_required
def criar_ajuste_estoque(request):
    contexto = get_contexto_operacional_usuario(request.user)
    matriz = contexto['matriz']
    loja_inicial = contexto.get('loja')

    form = AjusteEstoqueForm(
        request.POST or None,
        matriz=matriz,
        loja_inicial=loja_inicial,
    )

    if request.method == 'POST' and form.is_valid():
        dados = form.cleaned_data
        try:
            registrar_ajuste_estoque(
                matriz=matriz,
                loja=dados['loja'],
                produto=dados['produto'],
                origem=OrigemMovimentacao.MANUAL,
                quantidade_ajuste=dados['quantidade_ajuste'],
                chave_idempotencia=f'ajuste-manual:{matriz.pk}:{uuid.uuid4()}',
                motivo=dados['motivo'],
                usuario=request.user,
                documento_referencia=dados['documento_referencia'],
                origem_id='ajuste-manual',
                request=request,
            )
        except ValidationError as erro:
            _aplicar_erros_servico(form, erro)
        else:
            messages.success(
                request,
                'Ajuste de estoque registrado com sucesso.'
            )
            return redirect('estoque:lista_movimentacoes')

    return _render_operacao(
        request,
        form=form,
        titulo='Ajuste de estoque',
        subtitulo='Corrija diferenças identificadas em conferências ou inventários.',
        icone='bi-sliders',
        texto_botao='Registrar ajuste',
    )