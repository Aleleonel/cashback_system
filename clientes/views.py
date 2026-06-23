from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render

from cashback.selectors import (
    get_extrato_cliente,
    get_saldo_disponivel_cliente,
)
from core.services import get_contexto_operacional_usuario

from .models import Cliente
from .selectors import get_cliente_por_cpf

from django.db import models

from django.contrib import messages
from django.shortcuts import redirect
from .forms import ClienteForm

from django.core.paginator import Paginator


@login_required
def buscar_cliente_cpf(request):

    cpf = request.GET.get('cpf')

    if not cpf:
        return JsonResponse({'encontrado': False})

    try:
        contexto = get_contexto_operacional_usuario(request.user)

    except ValidationError as erro:
        return JsonResponse({
            'encontrado': False,
            'erro': erro.message
        }, status=400)

    cliente = get_cliente_por_cpf(
        matriz=contexto['matriz'],
        cpf=cpf
    )

    if not cliente:
        return JsonResponse({'encontrado': False})

    saldo_disponivel = get_saldo_disponivel_cliente(
        matriz=contexto['matriz'],
        cliente=cliente
    )

    return JsonResponse({
        'encontrado': True,
        'cliente_id': cliente.id,
        'nome': cliente.nome,
        'telefone': cliente.telefone or '',
        'email': cliente.email or '',
        'saldo_disponivel': str(saldo_disponivel),
        'data_nascimento': (
            cliente.data_nascimento.strftime('%d/%m/%Y')
            if cliente.data_nascimento
            else ''
        )
    })


@login_required
def extrato_cliente(request, cliente_id):

    contexto = get_contexto_operacional_usuario(request.user)

    cliente = get_object_or_404(
        Cliente.objects.select_related(
            'matriz',
            'loja_cadastro'
        ),
        id=cliente_id,
        matriz=contexto['matriz'],
        ativo=True
    )

    saldo = get_saldo_disponivel_cliente(
        matriz=contexto['matriz'],
        cliente=cliente
    )

    extrato = get_extrato_cliente(
        matriz=contexto['matriz'],
        cliente=cliente
    )

    return render(
        request,
        'clientes/extrato_cliente.html',
        {
            'cliente': cliente,
            'saldo': saldo,
            'extrato': extrato,
        }
    )

@login_required
def lista_clientes(request):

    contexto = get_contexto_operacional_usuario(
        request.user
    )

    busca = request.GET.get('q', '').strip()

    clientes = Cliente.objects.filter(
        matriz=contexto['matriz'],
        ativo=True
    ).only(
        'id',
        'nome',
        'cpf',
        'telefone',
        'email'
    )

    if busca:
        clientes = clientes.filter(
            models.Q(nome__icontains=busca) |
            models.Q(cpf__icontains=busca) |
            models.Q(telefone__icontains=busca)
        )

    clientes = clientes.order_by('nome')

    paginator = Paginator(clientes, 50)

    page = request.GET.get('page')

    clientes = paginator.get_page(page)

    return render(
        request,
        'clientes/lista_clientes.html',
        {
            'clientes': clientes,
            'busca': busca,
        }
    )

@login_required
def criar_cliente(request):

    contexto = get_contexto_operacional_usuario(request.user)

    if request.method == 'POST':
        form = ClienteForm(request.POST)

        if form.is_valid():
            cliente = form.save(commit=False)
            cliente.matriz = contexto['matriz']
            cliente.loja_cadastro = contexto['loja']
            cliente.save()

            messages.success(request, 'Cliente cadastrado com sucesso.')

            return redirect('clientes:lista_clientes')

    else:
        form = ClienteForm()

    return render(
        request,
        'clientes/form_cliente.html',
        {
            'form': form,
            'titulo': 'Novo Cliente',
        }
    )


@login_required
def editar_cliente(request, cliente_id):

    contexto = get_contexto_operacional_usuario(request.user)

    cliente = get_object_or_404(
        Cliente.objects.select_related('matriz', 'loja_cadastro'),
        id=cliente_id,
        matriz=contexto['matriz'],
    )

    if request.method == 'POST':
        form = ClienteForm(request.POST, instance=cliente)

        if form.is_valid():
            form.save()

            messages.success(request, 'Cliente atualizado com sucesso.')

            return redirect('clientes:lista_clientes')

    else:
        form = ClienteForm(instance=cliente)

    return render(
        request,
        'clientes/form_cliente.html',
        {
            'form': form,
            'titulo': 'Editar Cliente',
            'cliente': cliente,
        }
    )