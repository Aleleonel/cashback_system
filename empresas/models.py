import uuid

from django.db import models


class Matriz(models.Model):

    class StatusMatriz(models.TextChoices):
        IMPLANTACAO = 'implantacao', 'Em implantação'
        ATIVA = 'ativa', 'Ativa'
        SUSPENSA = 'suspensa', 'Suspensa'
        BLOQUEADA = 'bloqueada', 'Bloqueada'

    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        db_index=True
    )

    nome = models.CharField(max_length=150)

    cnpj = models.CharField(
        max_length=18,
        blank=True,
        null=True,
        unique=True,
        db_index=True
    )

    ativa = models.BooleanField(default=True)

    status = models.CharField(
        max_length=20,
        choices=StatusMatriz.choices,
        default=StatusMatriz.ATIVA,
        db_index=True
    )

    criada_em = models.DateTimeField(auto_now_add=True)
    atualizada_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['nome']
        indexes = [
            models.Index(fields=['nome']),
            models.Index(fields=['status']),
            models.Index(fields=['ativa', 'status']),
        ]

    def __str__(self):
        return self.nome


class Loja(models.Model):

    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        db_index=True
    )

    matriz = models.ForeignKey(
        Matriz,
        on_delete=models.PROTECT,
        related_name='lojas'
    )

    nome = models.CharField(max_length=150)

    cnpj = models.CharField(
        max_length=18,
        blank=True,
        null=True,
        db_index=True
    )

    telefone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        db_index=True
    )

    ativa = models.BooleanField(default=True)

    criada_em = models.DateTimeField(auto_now_add=True)
    atualizada_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['nome']
        constraints = [
            models.UniqueConstraint(
                fields=['matriz', 'cnpj'],
                name='unique_loja_por_matriz_cnpj'
            )
        ]
        indexes = [
            models.Index(fields=['matriz', 'nome']),
            models.Index(fields=['matriz', 'cnpj']),
            models.Index(fields=['matriz', 'ativa']),
        ]

    def __str__(self):
        return f'{self.nome} - {self.matriz.nome}'