from django.core.exceptions import ValidationError
from django.db import transaction

from rh.models import Funcionario


def _validar_vinculos(*, matriz, cargo, departamento):
    if cargo.matriz_id != matriz.id:
        raise ValidationError(
            "O cargo selecionado não pertence à matriz informada."
        )

    if departamento.matriz_id != matriz.id:
        raise ValidationError(
            "O departamento selecionado não pertence à matriz informada."
        )


@transaction.atomic
def criar_funcionario(
    *,
    matriz,
    cargo,
    departamento,
    nome_completo,
    cpf,
    rg="",
    email="",
    telefone="",
    data_nascimento=None,
    data_admissao,
    ativo=True,
):
    nome_completo = nome_completo.strip()
    cpf = cpf.strip()

    if not nome_completo:
        raise ValidationError("Informe o nome completo.")

    _validar_vinculos(
        matriz=matriz,
        cargo=cargo,
        departamento=departamento,
    )

    if Funcionario.objects.filter(
        matriz=matriz,
        cpf=cpf,
    ).exists():
        raise ValidationError(
            "Já existe um funcionário com esse CPF nesta matriz."
        )

    funcionario = Funcionario(
        matriz=matriz,
        cargo=cargo,
        departamento=departamento,
        nome_completo=nome_completo,
        cpf=cpf,
        rg=rg.strip(),
        email=email.strip().lower(),
        telefone=telefone.strip(),
        data_nascimento=data_nascimento,
        data_admissao=data_admissao,
        ativo=ativo,
    )

    funcionario.full_clean()
    funcionario.save()

    return funcionario


@transaction.atomic
def atualizar_funcionario(
    *,
    funcionario,
    cargo,
    departamento,
    nome_completo,
    cpf,
    rg,
    email,
    telefone,
    data_nascimento,
    data_admissao,
    ativo,
):
    nome_completo = nome_completo.strip()
    cpf = cpf.strip()

    _validar_vinculos(
        matriz=funcionario.matriz,
        cargo=cargo,
        departamento=departamento,
    )

    if Funcionario.objects.filter(
        matriz=funcionario.matriz,
        cpf=cpf,
    ).exclude(pk=funcionario.pk).exists():
        raise ValidationError(
            "Já existe um funcionário com esse CPF nesta matriz."
        )

    funcionario.cargo = cargo
    funcionario.departamento = departamento
    funcionario.nome_completo = nome_completo
    funcionario.cpf = cpf
    funcionario.rg = rg.strip()
    funcionario.email = email.strip().lower()
    funcionario.telefone = telefone.strip()
    funcionario.data_nascimento = data_nascimento
    funcionario.data_admissao = data_admissao
    funcionario.ativo = ativo

    funcionario.full_clean()
    funcionario.save()

    return funcionario


@transaction.atomic
def inativar_funcionario(funcionario):
    funcionario.ativo = False
    funcionario.full_clean()
    funcionario.save(update_fields=["ativo", "atualizado_em"])

    return funcionario