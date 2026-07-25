from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render

from rh.forms.funcionario_form import FuncionarioForm
from rh.models import Funcionario
from rh.selectors.funcionario_selector import buscar_funcionarios
from rh.services.funcionario_service import (
    atualizar_funcionario,
    criar_funcionario,
    inativar_funcionario,
)


def _matriz_do_usuario(request):
    return getattr(request.user, "matriz", None)


@login_required
def funcionario_list(request):
    matriz = _matriz_do_usuario(request)
    termo = request.GET.get("q", "").strip()
    status = request.GET.get("status", "")

    ativo = None

    if status == "ativos":
        ativo = True
    elif status == "inativos":
        ativo = False

    funcionarios = buscar_funcionarios(
        termo=termo,
        matriz=matriz,
        ativo=ativo,
    )

    return render(
        request,
        "rh/funcionario/list.html",
        {
            "funcionarios": funcionarios,
            "termo": termo,
            "status": status,
        },
    )


@login_required
def funcionario_create(request):
    matriz = _matriz_do_usuario(request)

    if request.method == "POST":
        form = FuncionarioForm(
            request.POST,
            matriz=matriz,
        )

        if form.is_valid():
            try:
                criar_funcionario(
                    matriz=matriz or form.cleaned_data["matriz"],
                    cargo=form.cleaned_data["cargo"],
                    departamento=form.cleaned_data["departamento"],
                    nome_completo=form.cleaned_data["nome_completo"],
                    cpf=form.cleaned_data["cpf"],
                    rg=form.cleaned_data["rg"],
                    email=form.cleaned_data["email"],
                    telefone=form.cleaned_data["telefone"],
                    data_nascimento=form.cleaned_data["data_nascimento"],
                    data_admissao=form.cleaned_data["data_admissao"],
                    ativo=form.cleaned_data["ativo"],
                )
            except ValidationError as exc:
                form.add_error(None, exc)
            else:
                messages.success(
                    request,
                    "Funcionário cadastrado com sucesso.",
                )
                return redirect("rh:funcionario_list")
    else:
        form = FuncionarioForm(
            matriz=matriz,
            initial={"matriz": matriz},
        )

    return render(
        request,
        "rh/funcionario/form.html",
        {
            "form": form,
            "titulo": "Novo Funcionário",
        },
    )


@login_required
def funcionario_update(request, pk):
    matriz = _matriz_do_usuario(request)

    filtros = {"pk": pk}

    if matriz is not None:
        filtros["matriz"] = matriz

    funcionario = get_object_or_404(
        Funcionario,
        **filtros,
    )

    if request.method == "POST":
        form = FuncionarioForm(
            request.POST,
            instance=funcionario,
            matriz=funcionario.matriz,
        )

        if form.is_valid():
            try:
                atualizar_funcionario(
                    funcionario=funcionario,
                    cargo=form.cleaned_data["cargo"],
                    departamento=form.cleaned_data["departamento"],
                    nome_completo=form.cleaned_data["nome_completo"],
                    cpf=form.cleaned_data["cpf"],
                    rg=form.cleaned_data["rg"],
                    email=form.cleaned_data["email"],
                    telefone=form.cleaned_data["telefone"],
                    data_nascimento=form.cleaned_data["data_nascimento"],
                    data_admissao=form.cleaned_data["data_admissao"],
                    ativo=form.cleaned_data["ativo"],
                )
            except ValidationError as exc:
                form.add_error(None, exc)
            else:
                messages.success(
                    request,
                    "Funcionário atualizado com sucesso.",
                )
                return redirect("rh:funcionario_list")
    else:
        form = FuncionarioForm(
            instance=funcionario,
            matriz=funcionario.matriz,
        )

    return render(
        request,
        "rh/funcionario/form.html",
        {
            "form": form,
            "titulo": "Editar Funcionário",
            "funcionario": funcionario,
        },
    )


@login_required
def funcionario_delete(request, pk):
    matriz = _matriz_do_usuario(request)

    filtros = {"pk": pk}

    if matriz is not None:
        filtros["matriz"] = matriz

    funcionario = get_object_or_404(
        Funcionario,
        **filtros,
    )

    if request.method == "POST":
        inativar_funcionario(funcionario)

        messages.success(
            request,
            "Funcionário inativado com sucesso.",
        )

        return redirect("rh:funcionario_list")

    return render(
        request,
        "rh/funcionario/delete.html",
        {
            "funcionario": funcionario,
        },
    )