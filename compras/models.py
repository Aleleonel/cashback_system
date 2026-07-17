import uuid

from django.db import models
from django.db.models.functions import Lower

from empresas.models import Matriz

from .choices import StatusFornecedor


class Fornecedor(models.Model):
    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        db_index=True,
    )

    matriz = models.ForeignKey(
        Matriz,
        on_delete=models.PROTECT,
        related_name='fornecedores',
    )

    razao_social = models.CharField(
        max_length=180,
        db_index=True,
    )

    nome_fantasia = models.CharField(
        max_length=180,
        blank=True,
        db_index=True,
    )

    cnpj = models.CharField(
        max_length=14,
        blank=True,
        db_index=True,
    )

    inscricao_estadual = models.CharField(
        max_length=30,
        blank=True,
    )

    telefone = models.CharField(
        max_length=20,
        blank=True,
    )

    whatsapp = models.CharField(
        max_length=20,
        blank=True,
    )

    email = models.EmailField(
        max_length=254,
        blank=True,
    )

    contato_principal = models.CharField(
        max_length=120,
        blank=True,
    )

    status = models.CharField(
        max_length=20,
        choices=StatusFornecedor.choices,
        default=StatusFornecedor.ATIVO,
        db_index=True,
    )

    observacoes = models.TextField(
        blank=True,
    )

    criado_em = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
    )

    atualizado_em = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = [
            'razao_social',
            'id',
        ]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    'matriz',
                    'cnpj',
                ],
                condition=~models.Q(cnpj=''),
                name='unique_fornecedor_matriz_cnpj',
            ),
            models.UniqueConstraint(
                Lower('razao_social'),
                'matriz',
                name='unique_fornecedor_matriz_razao_ci',
            ),
        ]

        indexes = [
            models.Index(
                fields=[
                    'matriz',
                    'status',
                ],
                name='compras_for_matriz_status_idx',
            ),
            models.Index(
                fields=[
                    'matriz',
                    'razao_social',
                ],
                name='compras_for_matriz_razao_idx',
            ),
            models.Index(
                fields=[
                    'matriz',
                    'cnpj',
                ],
                name='compras_for_matriz_cnpj_idx',
            ),
        ]

        verbose_name = 'Fornecedor'
        verbose_name_plural = 'Fornecedores'

    def __str__(self):
        return self.nome_fantasia or self.razao_social