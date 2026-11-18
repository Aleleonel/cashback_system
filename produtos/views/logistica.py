from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError
from django.core.exceptions import ValidationError
from django.http import HttpResponseNotAllowed
from django.forms.models import model_to_dict
from produtos.models.logistica import AuditoriaCadastroLogistico
from accounts.decorators import require_permission
from accounts.permissions import PERMISSAO_PRODUTOS_GERENCIAR_AUXILIARES
from core.services import get_contexto_operacional_usuario
from produtos.forms.logistica import ApresentacaoLogisticaForm, CaixaExpedicaoForm, CapacidadeCaixaForm, ReferenciaCapacidadeRefilForm, RegistroFonteLogisticaForm
from produtos.models.logistica import ApresentacaoProduto, ModeloCaixaExpedicao, CapacidadeReferenciaCaixa, ReferenciaCapacidadeRefil, RegistroFonteLogistica

MODELOS = {
    'apresentacoes': (ApresentacaoProduto, ApresentacaoLogisticaForm, 'Apresentacoes individuais'),
    'caixas': (ModeloCaixaExpedicao, CaixaExpedicaoForm, 'Caixas de expedicao'),
    'capacidades': (CapacidadeReferenciaCaixa, CapacidadeCaixaForm, 'Capacidades de referencia'),
    'referencias-refis': (ReferenciaCapacidadeRefil, ReferenciaCapacidadeRefilForm, 'Referencias de refis'),
    'fontes-planilha': (RegistroFonteLogistica, RegistroFonteLogisticaForm, 'Linhas originais da planilha'),
}

@login_required
@require_permission(PERMISSAO_PRODUTOS_GERENCIAR_AUXILIARES)
def lista_logistica(request, tipo):
    if tipo not in MODELOS:
        from django.http import Http404
        raise Http404
    matriz = get_contexto_operacional_usuario(request.user)['matriz']
    modelo, _, titulo = MODELOS[tipo]
    itens = modelo.objects.filter(matriz=matriz).order_by('pk')
    return render(request, 'produtos/logistica/lista.html', {'pagina': Paginator(itens, 25).get_page(request.GET.get('page')), 'tipo': tipo, 'titulo': titulo, 'pode_inativar': tipo in ('apresentacoes', 'caixas')})

@login_required
@require_permission(PERMISSAO_PRODUTOS_GERENCIAR_AUXILIARES)
def editar_logistica(request, tipo, item_id=None):
    if tipo not in MODELOS:
        from django.http import Http404
        raise Http404
    matriz = get_contexto_operacional_usuario(request.user)['matriz']
    modelo, form_class, titulo = MODELOS[tipo]
    item = get_object_or_404(modelo, pk=item_id, matriz=matriz) if item_id else None
    kwargs = {'instance': item}
    if tipo in ('capacidades', 'referencias-refis'): kwargs['matriz'] = matriz
    form = form_class(request.POST or None, **kwargs)
    if request.method == 'POST' and form.is_valid():
        obj = form.save(commit=False)
        obj.matriz = matriz
        try:
            with transaction.atomic():
                antes = _snapshot(modelo.objects.get(pk=item.pk)) if item else {}
                obj.full_clean()
                obj.save()
                _audit(request, matriz, tipo, obj.pk, 'EDICAO' if item else 'CRIACAO', antes, _snapshot(obj))
        except (IntegrityError, Exception) as exc:
            from django.core.exceptions import ValidationError
            if not isinstance(exc, (IntegrityError, ValidationError)):
                raise
            form.add_error(None, 'Dados invalidos ou cadastro duplicado. Confira os campos e tente novamente.')
        else:
            messages.success(request, 'Cadastro salvo com sucesso.')
            return redirect('produtos:logistica_lista', tipo=tipo)
    return render(request, 'produtos/logistica/form.html', {'form': form, 'tipo': tipo, 'titulo': titulo, 'edicao': bool(item)})


def _snapshot(obj):
    if obj is None:
        return {}
    return {f.attname: str(getattr(obj, f.attname)) if getattr(obj, f.attname) is not None else None
            for f in obj._meta.concrete_fields if not f.primary_key}


def _audit(request, matriz, tipo, pk, acao, antes, depois):
    AuditoriaCadastroLogistico.objects.create(
        matriz=matriz, usuario=request.user, tipo=tipo, objeto_id=pk,
        acao=acao, antes=antes, depois=depois)


@login_required
@require_permission(PERMISSAO_PRODUTOS_GERENCIAR_AUXILIARES)
def acao_logistica(request, tipo, item_id):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    if tipo not in MODELOS:
        from django.http import Http404
        raise Http404
    matriz = get_contexto_operacional_usuario(request.user)['matriz']
    modelo = MODELOS[tipo][0]
    with transaction.atomic():
        item = get_object_or_404(modelo.objects.select_for_update(), pk=item_id, matriz=matriz)
        acao = request.POST.get('acao')
        if acao in ('inativar', 'reativar') and tipo in ('apresentacoes', 'caixas'):
            antes = _snapshot(item)
            item.ativo = acao == 'reativar'
            item.full_clean()
            item.save(update_fields=['ativo'])
            _audit(request, matriz, tipo, item_id, acao.upper(), antes, _snapshot(item))
            messages.success(request, 'Status atualizado com sucesso.')
        elif acao == 'excluir':
            # Fail closed: records referenced by any reverse relationship cannot be removed.
            # This also preserves imported provenance, and avoids cascading deletes.
            dependencias = []
            for rel in item._meta.related_objects:
                if rel.related_model is AuditoriaCadastroLogistico:
                    continue
                if rel.field.remote_field.parent_link:
                    dependencias.append(rel.related_model._meta.label)
                    continue
                filtro = {rel.field.name: item}
                if rel.related_model._default_manager.filter(**filtro).exists():
                    dependencias.append(rel.related_model._meta.label)
            if dependencias:
                messages.error(request, 'Exclusao bloqueada: cadastro possui referencias. Utilize inativacao quando disponivel.')
            else:
                antes = _snapshot(item)
                try:
                    item.delete()
                except ProtectedError:
                    messages.error(request, 'Exclusao bloqueada por dependencias protegidas.')
                else:
                    _audit(request, matriz, tipo, item_id, 'EXCLUSAO', antes, {})
                    messages.success(request, 'Cadastro excluido e registrado na auditoria.')
        else:
            messages.error(request, 'Acao invalida para este cadastro.')
    return redirect('produtos:logistica_lista', tipo=tipo)
