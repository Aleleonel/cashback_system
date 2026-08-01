from django.core.validators import MinLengthValidator
from django.db import models

from empresas.models import Matriz

from .cargo import Cargo
from .departamento import Departamento


class Funcionario(models.Model):
    """
    Cadastro principal dos funcionários da matriz.
    """

    matriz = models.ForeignKey(
        Matriz,
        on_delete=models.CASCADE,
        related_name="funcionarios",
        verbose_name="Matriz",
    )

    cargo = models.ForeignKey(
        Cargo,
        on_delete=models.PROTECT,
        related_name="funcionarios",
        verbose_name="Cargo",
    )

    departamento = models.ForeignKey(
        Departamento,
        on_delete=models.PROTECT,
        related_name="funcionarios",
        verbose_name="Departamento",
    )

    nome_completo = models.CharField(
        "Nome completo",
        max_length=150,
        validators=[MinLengthValidator(3)],
    )

    cpf = models.CharField(
        "CPF",
        max_length=14,
    )

    rg = models.CharField(
        "RG",
        max_length=20,
        blank=True,
        default="",
    )

    email = models.EmailField(
        "E-mail",
        blank=True,
        default="",
    )

    telefone = models.CharField(
        "Telefone",
        max_length=20,
        blank=True,
        default="",
    )

    data_nascimento = models.DateField(
        "Data de nascimento",
        null=True,
        blank=True,
    )

    data_admissao = models.DateField(
        "Data de admissão",
    )

    ativo = models.BooleanField(
        "Ativo",
        default=True,
    )

    criado_em = models.DateTimeField(
        "Criado em",
        auto_now_add=True,
    )

    atualizado_em = models.DateTimeField(
        "Atualizado em",
        auto_now=True,
    )

    class Meta:
        db_table = "rh_funcionario"
        verbose_name = "Funcionário"
        verbose_name_plural = "Funcionários"
        ordering = ["nome_completo"]

        constraints = [
            models.UniqueConstraint(
                fields=["matriz", "cpf"],
                name="uk_rh_funcionario_matriz_cpf",
            ),
        ]

        indexes = [
            models.Index(
                fields=["matriz", "ativo"],
                name="idx_rh_func_matriz_ativo",
            ),
            models.Index(
                fields=["nome_completo"],
                name="idx_rh_func_nome",
            ),
            models.Index(
                fields=["cpf"],
                name="idx_rh_func_cpf",
            ),
        ]

    def __str__(self):
        return self.nome_completo