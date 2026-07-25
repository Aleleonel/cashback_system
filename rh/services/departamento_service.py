from django.core.exceptions import ValidationError
from django.db import transaction

from rh.models import Departamento


@transaction.atomic
def criar_departamento(
    *,
    matriz,
    nome,
    descricao="",
    ativo=True,
):
    """
    Cria um novo departamento.
    """

    nome = nome.strip()
    descricao = descricao.strip()

    if not nome:
        raise ValidationError(
            "Informe o nome do departamento."
        )

    if Departamento.objects.filter(
        matriz=matriz,
        nome__iexact=nome,
    ).exists():
        raise ValidationError(
            "Já existe um departamento com esse nome nesta matriz."
        )

    departamento = Departamento(
        matriz=matriz,
        nome=nome,
        descricao=descricao,
        ativo=ativo,
    )

    departamento.full_clean()
    departamento.save()

    return departamento


@transaction.atomic
def atualizar_departamento(
    *,
    departamento,
    nome,
    descricao,
    ativo,
):
    """
    Atualiza um departamento existente.
    """

    nome = nome.strip()
    descricao = descricao.strip()

    if not nome:
        raise ValidationError(
            "Informe o nome do departamento."
        )

    if Departamento.objects.filter(
        matriz=departamento.matriz,
        nome__iexact=nome,
    ).exclude(pk=departamento.pk).exists():
        raise ValidationError(
            "Já existe um departamento com esse nome nesta matriz."
        )

    departamento.nome = nome
    departamento.descricao = descricao
    departamento.ativo = ativo

    departamento.full_clean()
    departamento.save()

    return departamento


@transaction.atomic
def excluir_departamento(departamento):
    """
    Inativa um departamento sem realizar exclusao fisica.
    """

    departamento.ativo = False
    departamento.full_clean()
    departamento.save(update_fields=["ativo", "atualizado_em"])

    return departamento