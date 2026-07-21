from django.db import models
from django.core.validators import MinLengthValidator

from empresas.models import Matriz


class Cargo(models.Model):
    """
    Cargos da empresa.

    Exemplos:
        - Gerente
        - Caixa
        - Vendedor
        - Estoquista
        - Supervisor
    """

    matriz = models.ForeignKey(
        Matriz,
        on_delete=models.CASCADE,
        related_name="cargos",
        verbose_name="Matriz",
    )

    nome = models.CharField(
        "Nome",
        max_length=100,
        validators=[MinLengthValidator(2)],
    )

    descricao = models.TextField(
        "Descrição",
        blank=True,
        default="",
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
        db_table = "rh_cargo"

        verbose_name = "Cargo"

        verbose_name_plural = "Cargos"

        ordering = [
            "nome",
        ]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "matriz",
                    "nome",
                ],
                name="uk_rh_cargo_matriz_nome",
            ),
        ]

        indexes = [
            models.Index(
                fields=[
                    "matriz",
                    "ativo",
                ],
                name="idx_rh_cargo_matriz_ativo",
            ),
            models.Index(
                fields=[
                    "nome",
                ],
                name="idx_rh_cargo_nome",
            ),
        ]

    def __str__(self):
        return self.nome