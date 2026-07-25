from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render

from rh.forms.departamento_form import DepartamentoForm
from rh.models import Departamento
from rh.selectors.departamento_selector import listar_departamentos
from rh.services.departamento_service import (
    atualizar_departamento,
    criar_departamento,
    excluir_departamento,
)


def _matriz_do_usuario(request):
    return getattr(request.user, "matriz", None)


@login_required
def departamento_list(request):
    matriz = _matriz_do_usuario(request)

    departamentos = listar_departamentos(
        matriz=matriz,
        ativo=None,
    )

    context = {
        "departamentos": departamentos,
    }

    return render(
        request,
        "rh/departamento/list.html",
        context,
    )


@login_required
def departamento_create(request):
    matriz = _matriz_do_usuario(request)

    if request.method == "POST":
        form = DepartamentoForm(request.POST)

        if form.is_valid():
            try:
                criar_departamento(
                    matriz=matriz or form.cleaned_data["matriz"],
                    nome=form.cleaned_data["nome"],
                    descricao=form.cleaned_data["descricao"],
                    ativo=form.cleaned_data["ativo"],
                )
            except ValidationError as exc:
                form.add_error(None, exc)
            else:
                messages.success(
                    request,
                    "Departamento cadastrado com sucesso.",
                )

                return redirect("rh:departamento_list")
    else:
        form = DepartamentoForm(
            initial={
                "matriz": matriz,
            }
        )

    if matriz is not None:
        form.fields["matriz"].queryset = (
            form.fields["matriz"].queryset.filter(pk=matriz.pk)
        )
        form.fields["matriz"].initial = matriz

    return render(
        request,
        "rh/departamento/form.html",
        {
            "form": form,
            "titulo": "Novo Departamento",
        },
    )


@login_required
def departamento_update(request, pk):
    matriz = _matriz_do_usuario(request)

    filtros = {
        "pk": pk,
    }

    if matriz is not None:
        filtros["matriz"] = matriz

    departamento = get_object_or_404(
        Departamento,
        **filtros,
    )

    if request.method == "POST":
        form = DepartamentoForm(
            request.POST,
            instance=departamento,
        )

        if form.is_valid():
            try:
                atualizar_departamento(
                    departamento=departamento,
                    nome=form.cleaned_data["nome"],
                    descricao=form.cleaned_data["descricao"],
                    ativo=form.cleaned_data["ativo"],
                )
            except ValidationError as exc:
                form.add_error(None, exc)
            else:
                messages.success(
                    request,
                    "Departamento atualizado com sucesso.",
                )

                return redirect("rh:departamento_list")
    else:
        form = DepartamentoForm(instance=departamento)

    form.fields["matriz"].queryset = (
        form.fields["matriz"].queryset.filter(
            pk=departamento.matriz_id
        )
    )

    return render(
        request,
        "rh/departamento/form.html",
        {
            "form": form,
            "titulo": "Editar Departamento",
        },
    )


@login_required
def departamento_delete(request, pk):
    matriz = _matriz_do_usuario(request)

    filtros = {
        "pk": pk,
    }

    if matriz is not None:
        filtros["matriz"] = matriz

    departamento = get_object_or_404(
        Departamento,
        **filtros,
    )

    if request.method == "POST":
        excluir_departamento(departamento)

        messages.success(
            request,
            "Departamento inativado com sucesso.",
        )

        return redirect("rh:departamento_list")

    return render(
        request,
        "rh/departamento/delete.html",
        {
            "departamento": departamento,
        },
    )