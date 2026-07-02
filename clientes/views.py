from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from io import BytesIO

from django.http import HttpResponse
from openpyxl import Workbook

from auditoria.models import RegistroAuditoria
from auditoria.services import registrar_auditoria

from cashback.selectors import (
    get_extrato_cliente,
    get_saldo_disponivel_cliente,
)
from core.services import get_contexto_operacional_usuario

from .models import Cliente


from django.db import models

from django.contrib import messages
from django.shortcuts import redirect

from .forms import (
    ClienteForm,
    ImportarClientesForm,
)

from .services import (
    importar_clientes_validados,
    validar_planilha_clientes,
)

from .selectors import (
    aplicar_busca_clientes,
    get_cliente_por_cpf,
)

from accounts.decorators import require_permission

from accounts.permissions import (
    PERMISSAO_CLIENTES_CRIAR,
    PERMISSAO_CLIENTES_EDITAR,
    PERMISSAO_CLIENTES_IMPORTAR,
    PERMISSAO_CLIENTES_VISUALIZAR,
)

from django.core.paginator import Paginator


@login_required
@require_permission(PERMISSAO_CLIENTES_VISUALIZAR)
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
    saldo_disponivel = saldo_disponivel.quantize(Decimal('0.01'))

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
@require_permission(PERMISSAO_CLIENTES_VISUALIZAR)
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
@require_permission(PERMISSAO_CLIENTES_VISUALIZAR)
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
        'nome_normalizado',
        'cpf',
        'cpf_normalizado',
        'telefone',
        'telefone_normalizado',
        'email',
        'email_normalizado',
    )

    if busca:
        clientes = aplicar_busca_clientes(
            clientes,
            busca
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
@require_permission(PERMISSAO_CLIENTES_CRIAR)
def criar_cliente(request):

    contexto = get_contexto_operacional_usuario(request.user)

    if request.method == 'POST':
        form = ClienteForm(request.POST)

        if form.is_valid():
            cliente = form.save(commit=False)
            cliente.matriz = contexto['matriz']
            cliente.loja_cadastro = contexto['loja']

            cliente.save()

            registrar_auditoria(
                usuario=request.user,
                matriz=contexto['matriz'],
                loja=contexto['loja'],
                acao=RegistroAuditoria.ACAO_CRIAR,
                recurso='clientes.cliente',
                recurso_id=cliente.id,
                descricao=f'Cliente criado: {cliente.nome}',
                request=request
            )

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
@require_permission(PERMISSAO_CLIENTES_EDITAR)
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
            cliente = form.save()

            registrar_auditoria(
                usuario=request.user,
                matriz=contexto['matriz'],
                loja=contexto['loja'],
                acao=RegistroAuditoria.ACAO_EDITAR,
                recurso='clientes.cliente',
                recurso_id=cliente.id,
                descricao=f'Cliente editado: {cliente.nome}',
                request=request
            )

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

@login_required
@require_permission(PERMISSAO_CLIENTES_IMPORTAR)
def importar_clientes(request):

    contexto = get_contexto_operacional_usuario(request.user)

    if request.method == 'POST':
        form = ImportarClientesForm(request.POST, request.FILES)

        if form.is_valid():
            resultado = validar_planilha_clientes(
                arquivo=form.cleaned_data['arquivo'],
                matriz=contexto['matriz']
            )

            if not resultado['valido']:
                messages.error(request, resultado['erro_estrutura'])

            else:
                resultado['possui_validos'] = (
                    resultado['resumo']['validos'] > 0
                )

                request.session['importacao_clientes_linhas'] = resultado['linhas']

                return render(
                    request,
                    'clientes/confirmar_importacao.html',
                    {
                        'resultado': resultado,
                    }
                )

    else:
        form = ImportarClientesForm()

    return render(
        request,
        'clientes/importar_clientes.html',
        {
            'form': form,
        }
    )


@login_required
@require_permission(PERMISSAO_CLIENTES_IMPORTAR)
def confirmar_importacao_clientes(request):

    contexto = get_contexto_operacional_usuario(request.user)

    linhas = request.session.get('importacao_clientes_linhas')

    if not linhas:
        messages.error(request, 'Nenhuma importação pendente encontrada.')

        return redirect('clientes:importar_clientes')

    resultado = importar_clientes_validados(
        matriz=contexto['matriz'],
        loja=contexto['loja'],
        linhas=linhas
    )
    
    registrar_auditoria(
        usuario=request.user,
        matriz=contexto['matriz'],
        loja=contexto['loja'],
        acao=RegistroAuditoria.ACAO_IMPORTAR,
        recurso='clientes.importacao',
        descricao=(
            f"Importação de clientes concluída. "
            f"Criados: {resultado['criados']}. "
            f"Atualizados: {resultado['atualizados']}."
        ),
        request=request
    )

    del request.session['importacao_clientes_linhas']

    messages.success(
        request,
        f"Importação concluída. Criados: {resultado['criados']}. Atualizados: {resultado['atualizados']}."
    )

    return redirect('clientes:lista_clientes')


@login_required
@require_permission(PERMISSAO_CLIENTES_IMPORTAR)
def baixar_modelo_importacao_clientes(request):

    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = 'Clientes'

    colunas = [
        'Nome',
        'CPF',
        'Nascimento',
        'Celular',
        'E-mail',
    ]

    worksheet.append(colunas)

    worksheet.append([
        'João Silva',
        '12345678900',
        '01/01/1990',
        '11999999999',
        'joao@email.com',
    ])

    for column in worksheet.columns:
        max_length = 0
        column_letter = column[0].column_letter

        for cell in column:
            if cell.value:
                max_length = max(
                    max_length,
                    len(str(cell.value))
                )

        worksheet.column_dimensions[column_letter].width = max_length + 4

    arquivo = BytesIO()
    workbook.save(arquivo)
    arquivo.seek(0)

    response = HttpResponse(
        arquivo,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

    response['Content-Disposition'] = (
        'attachment; filename="modelo_importacao_clientes.xlsx"'
    )

    return response