import uuid
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.shortcuts import redirect, render

from accounts.decorators import require_permission
from accounts.permissions import PERMISSAO_CASHBACK_NOVA_COMPRA
from auditoria.models import RegistroAuditoria
from auditoria.services import registrar_auditoria
from core.services import get_contexto_operacional_usuario

from .forms import NovaCompraForm
from .models import LancamentoCashback
from .services import registrar_venda


@login_required
@require_permission(PERMISSAO_CASHBACK_NOVA_COMPRA)
def nova_compra(request):

    try:
        contexto_operacional = get_contexto_operacional_usuario(request.user)

    except ValidationError as erro:
        messages.error(request, erro.message)

        return render(
            request,
            'cashback/nova_compra.html',
            {
                'form': NovaCompraForm(initial={
                    'chave_idempotencia': uuid.uuid4(),
                }),
                'bloquear_formulario': True,
            }
        )

    if request.method == 'POST':
        form = NovaCompraForm(request.POST)

        if form.is_valid():

            try:
                resultado = registrar_venda(
                    matriz=contexto_operacional['matriz'],
                    loja=contexto_operacional['loja'],
                    usuario=request.user,
                    chave_idempotencia=form.cleaned_data['chave_idempotencia'],
                    cpf=form.cleaned_data['cpf'],
                    nome=form.cleaned_data['nome'],
                    telefone=form.cleaned_data['telefone'],
                    email=form.cleaned_data['email'],
                    data_nascimento=form.cleaned_data['data_nascimento'],
                    valor_compra=form.cleaned_data['valor_compra'],
                    valor_cashback_usado=form.cleaned_data['valor_cashback_usado'],
                    aceita_email=form.cleaned_data['aceita_email'],
                    aceita_sms=form.cleaned_data['aceita_sms'],
                    observacao=form.cleaned_data['observacao'],
                    aplicar_voucher=form.cleaned_data['aplicar_voucher'],
                    codigo_voucher=form.cleaned_data['codigo_voucher'],
                )

            except ValidationError as erro:
                messages.error(request, erro.message)

            except IntegrityError:
                lancamento_existente = (
                    LancamentoCashback.objects
                    .filter(
                        matriz=contexto_operacional['matriz'],
                        chave_idempotencia=(
                            form.cleaned_data['chave_idempotencia']
                        ),
                    )
                    .select_related(
                        'cliente',
                    )
                    .first()
                )

                if not lancamento_existente:
                    raise

                messages.warning(
                    request,
                    'Esta compra já foi registrada anteriormente.'
                )

                return redirect('cashback:nova_compra')

            else:
                lancamento = resultado['compra']

                if resultado['duplicada']:
                    messages.warning(
                        request,
                        'Esta compra já foi registrada anteriormente.'
                    )

                    return redirect('cashback:nova_compra')

                messages.success(
                    request,
                    (
                        'Compra registrada. '
                        f'Cashback gerado: R$ {lancamento.valor_cashback}.'
                    )
                )

                registrar_auditoria(
                    usuario=request.user,
                    matriz=contexto_operacional['matriz'],
                    loja=contexto_operacional['loja'],
                    acao=RegistroAuditoria.ACAO_CRIAR,
                    recurso='cashback.compra',
                    recurso_id=lancamento.id,
                    descricao=(
                        f'Compra registrada para {lancamento.cliente.nome}. '
                        f'Valor da compra: R$ {lancamento.valor_compra}. '
                        f'Cashback gerado: R$ {lancamento.valor_cashback}.'
                    ),
                    request=request
                )

                return redirect('cashback:nova_compra')

    else:
        form = NovaCompraForm(initial={
            'chave_idempotencia': uuid.uuid4(),
        })

    return render(
        request,
        'cashback/nova_compra.html',
        {
            'form': form,
            'bloquear_formulario': False,
            'loja_operacional': contexto_operacional['loja'],
        }
    )