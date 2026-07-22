from django.core.validators import MinLengthValidator
from django.db import models

from empresas.models import Matriz


class Departamento(models.Model):
    """
    Departamentos da empresa.

    Exemplos:
        - Administrativo
        - Comercial
        - Financeiro
        - Recursos Humanos
        - Tecnologia
    """

    matriz = models.ForeignKey(
        Matriz,
        on_delete=models.CASCADE,
        related_name="departamentos",
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
        db_table = "rh_departamento"
        verbose_name = "Departamento"
        verbose_name_plural = "Departamentos"
        ordering = ["nome"]

        constraints = [
            models.UniqueConstraint(
                fields=["matriz", "nome"],
                name="uk_rh_departamento_matriz_nome",
            ),
        ]

        indexes = [
            models.Index(
                fields=["matriz", "ativo"],
                name="idx_rh_depart_matriz_ativo",
            ),
            models.Index(
                fields=["nome"],
                name="idx_rh_depart_nome",
            ),
        ]

    def __str__(self):
        return self.nome