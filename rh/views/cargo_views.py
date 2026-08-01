from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from rh.forms.cargo_form import CargoForm
from rh.models import Cargo
from rh.selectors.cargo_selector import listar_cargos
from rh.services.cargo_service import (
    atualizar_cargo,
    criar_cargo,
    excluir_cargo,
)


@login_required
def cargo_list(request):
    matriz = getattr(request.user, "matriz", None)

    cargos = listar_cargos(matriz=matriz)

    context = {
        "cargos": cargos,
    }

    return render(
        request,
        "rh/cargo/list.html",
        context,
    )


@login_required
def cargo_create(request):
    if request.method == "POST":
        form = CargoForm(request.POST)

        if form.is_valid():
            criar_cargo(
                matriz=form.cleaned_data["matriz"],
                nome=form.cleaned_data["nome"],
                descricao=form.cleaned_data["descricao"],
                ativo=form.cleaned_data["ativo"],
            )

            messages.success(
                request,
                "Cargo cadastrado com sucesso.",
            )

            return redirect("rh:cargo_list")
    else:
        form = CargoForm()

    return render(
        request,
        "rh/cargo/form.html",
        {
            "form": form,
            "titulo": "Novo Cargo",
        },
    )


@login_required
def cargo_update(request, pk):
    cargo = get_object_or_404(
        Cargo,
        pk=pk,
    )

    if request.method == "POST":
        form = CargoForm(
            request.POST,
            instance=cargo,
        )

        if form.is_valid():
            atualizar_cargo(
                cargo=cargo,
                nome=form.cleaned_data["nome"],
                descricao=form.cleaned_data["descricao"],
                ativo=form.cleaned_data["ativo"],
            )

            messages.success(
                request,
                "Cargo atualizado com sucesso.",
            )

            return redirect("rh:cargo_list")
    else:
        form = CargoForm(instance=cargo)

    return render(
        request,
        "rh/cargo/form.html",
        {
            "form": form,
            "titulo": "Editar Cargo",
        },
    )


@login_required
def cargo_delete(request, pk):
    cargo = get_object_or_404(
        Cargo,
        pk=pk,
    )

    if request.method == "POST":
        excluir_cargo(cargo)

        messages.success(
            request,
            "Cargo removido com sucesso.",
        )

        return redirect("rh:cargo_list")

    return render(
        request,
        "rh/cargo/delete.html",
        {
            "cargo": cargo,
        },
    )