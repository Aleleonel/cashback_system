from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import NovaCompraForm
from .services import registrar_compra


@login_required
def nova_compra(request):

    if request.method == 'POST':
        form = NovaCompraForm(request.POST)

        if form.is_valid():
            lancamento = registrar_compra(
                matriz=request.user.matriz,
                loja=request.user.lojas.first(),
                cpf=form.cleaned_data['cpf'],
                nome=form.cleaned_data['nome'],
                telefone=form.cleaned_data['telefone'],
                email=form.cleaned_data['email'],
                data_nascimento=form.cleaned_data['data_nascimento'],
                valor_compra=form.cleaned_data['valor_compra'],
                aceita_email=form.cleaned_data['aceita_email'],
                aceita_sms=form.cleaned_data['aceita_sms'],
                observacao=form.cleaned_data['observacao'],
            )

            messages.success(
                request,
                f'Compra registrada. Cashback gerado: R$ {lancamento.valor_cashback}.'
            )

            return redirect('cashback:nova_compra')

    else:
        form = NovaCompraForm()

    return render(
        request,
        'cashback/nova_compra.html',
        {
            'form': form
        }
    )