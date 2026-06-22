import uuid

from django.db import models

from empresas.models import Matriz, Loja


class Cliente(models.Model):

    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        db_index=True
    )

    matriz = models.ForeignKey(
        Matriz,
        on_delete=models.CASCADE,
        related_name='clientes'
    )

    loja_cadastro = models.ForeignKey(
        Loja,
        on_delete=models.PROTECT,
        related_name='clientes_cadastrados'
    )

    nome = models.CharField(max_length=150)

    cpf = models.CharField(
        max_length=14,
        db_index=True
    )

    telefone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        db_index=True
    )

    data_nascimento = models.DateField(
        blank=True,
        null=True,
        db_index=True
    )

    email = models.EmailField(
        blank=True,
        null=True,
        db_index=True
    )

    aceita_email = models.BooleanField(default=True)
    aceita_sms = models.BooleanField(default=False)

    ativo = models.BooleanField(default=True)

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['nome']
        constraints = [
            models.UniqueConstraint(
                fields=['matriz', 'cpf'],
                name='unique_cliente_por_matriz_cpf'
            )
        ]
        indexes = [
            models.Index(fields=['matriz', 'cpf']),
            models.Index(fields=['matriz', 'nome']),
            models.Index(fields=['matriz', 'telefone']),
            models.Index(fields=['matriz', 'email']),
            models.Index(fields=['matriz', 'data_nascimento']),
            models.Index(fields=['matriz', 'ativo']),
            models.Index(fields=['loja_cadastro', 'criado_em']),
        ]

    def __str__(self):
        return f'{self.nome} - {self.cpf}'