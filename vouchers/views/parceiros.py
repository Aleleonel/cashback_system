from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.core.exceptions import ValidationError
from accounts.decorators import require_permission
from accounts.permissions import PERMISSAO_VOUCHERS_GERENCIAR
from auditoria.models import RegistroAuditoria
from auditoria.services import registrar_auditoria
from core.services import get_contexto_operacional_usuario
from vouchers.forms import ParceiroForm
from vouchers.models import Parceiro

@login_required
@require_permission(PERMISSAO_VOUCHERS_GERENCIAR)
def lista_parceiros(request):
    contexto=get_contexto_operacional_usuario(request.user)
    parceiros=Parceiro.objects.filter(matriz=contexto['matriz']).order_by('nome')
    return render(request,'vouchers/parceiros_lista.html',{'parceiros':parceiros})

@login_required
@require_permission(PERMISSAO_VOUCHERS_GERENCIAR)
def criar_parceiro_view(request):
    contexto=get_contexto_operacional_usuario(request.user)
    form=ParceiroForm(request.POST or None)
    if request.method=='POST' and form.is_valid():
        parceiro=form.save(commit=False)
        parceiro.matriz=contexto['matriz']
        try:
            parceiro.full_clean()
        except ValidationError as exc:
            for campo, erros in exc.message_dict.items():
                destino = campo if campo in form.fields else None
                for erro in erros:
                    form.add_error(destino, erro)
        else:
            parceiro.save()
            registrar_auditoria(
                usuario=request.user,
                matriz=contexto['matriz'],
                loja=None,
                acao=RegistroAuditoria.ACAO_CRIAR,
                recurso='parceiro',
                recurso_id=parceiro.id,
                descricao=f'Parceiro criado: {parceiro.nome}',
                request=request,
            )
            messages.success(request,'Parceiro cadastrado com sucesso.')
            return redirect('vouchers:lista_parceiros')
    return render(request,'vouchers/parceiro_form.html',{'form':form,'titulo':'Novo Parceiro'})

@login_required
@require_permission(PERMISSAO_VOUCHERS_GERENCIAR)
def editar_parceiro_view(request,parceiro_id):
    contexto=get_contexto_operacional_usuario(request.user)
    parceiro=get_object_or_404(Parceiro,id=parceiro_id,matriz=contexto['matriz'])
    form=ParceiroForm(request.POST or None,instance=parceiro)
    if request.method=='POST' and form.is_valid():
        parceiro=form.save(commit=False)
        parceiro.matriz=contexto['matriz']
        try:
            parceiro.full_clean()
        except ValidationError as exc:
            for campo, erros in exc.message_dict.items():
                destino = campo if campo in form.fields else None
                for erro in erros:
                    form.add_error(destino, erro)
        else:
            parceiro.save()
            registrar_auditoria(
                usuario=request.user,
                matriz=contexto['matriz'],
                loja=None,
                acao=RegistroAuditoria.ACAO_EDITAR,
                recurso='parceiro',
                recurso_id=parceiro.id,
                descricao=f'Parceiro alterado: {parceiro.nome}',
                request=request,
            )
            messages.success(request,'Parceiro atualizado com sucesso.')
            return redirect('vouchers:lista_parceiros')
    return render(request,'vouchers/parceiro_form.html',{'form':form,'titulo':'Editar Parceiro','parceiro':parceiro})
