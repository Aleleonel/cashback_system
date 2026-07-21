from django.db import transaction
from django.core.exceptions import ValidationError

from rh.models import Cargo


@transaction.atomic
def criar_cargo(
    *,
    matriz,
    nome,
    descricao="",
    ativo=True,
):
    """
    Cria um novo cargo.
    """

    nome = nome.strip()

    if not nome:
        raise ValidationError("Informe o nome do cargo.")

    if Cargo.objects.filter(
        matriz=matriz,
        nome__iexact=nome,
    ).exists():
        raise ValidationError(
            "Já existe um cargo com esse nome nesta matriz."
        )

    cargo = Cargo.objects.create(
        matriz=matriz,
        nome=nome,
        descricao=descricao.strip(),
        ativo=ativo,
    )

    return cargo


@transaction.atomic
def atualizar_cargo(
    *,
    cargo,
    nome,
    descricao,
    ativo,
):
    """
    Atualiza um cargo existente.
    """

    nome = nome.strip()

    if not nome:
        raise ValidationError("Informe o nome do cargo.")

    if Cargo.objects.filter(
        matriz=cargo.matriz,
        nome__iexact=nome,
    ).exclude(pk=cargo.pk).exists():
        raise ValidationError(
            "Já existe um cargo com esse nome nesta matriz."
        )

    cargo.nome = nome
    cargo.descricao = descricao.strip()
    cargo.ativo = ativo

    cargo.full_clean()
    cargo.save()

    return cargo


@transaction.atomic
def excluir_cargo(cargo):
    """
    Remove um cargo.
    """

    cargo.delete()