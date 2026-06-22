import uuid
from django.utils import timezone
from django.contrib.auth.models import AbstractUser
from django.db import models

from empresas.models import Matriz, Loja


class Usuario(AbstractUser):

    PERFIL_MASTER = 'master'
    PERFIL_ADMIN_LOJA = 'admin_loja'
    PERFIL_OPERADOR = 'operador'

    PERFIL_CHOICES = [
        (PERFIL_MASTER, 'Master'),
        (PERFIL_ADMIN_LOJA, 'Administrador da Loja'),
        (PERFIL_OPERADOR, 'Operador'),
    ]

    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        db_index=True
    )

    perfil = models.CharField(
        max_length=20,
        choices=PERFIL_CHOICES,
        default=PERFIL_OPERADOR,
        db_index=True
    )

    matriz = models.ForeignKey(
        Matriz,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name='usuarios'
    )

    lojas = models.ManyToManyField(
        Loja,
        blank=True,
        related_name='usuarios'
    )

    telefone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        db_index=True
    )

    ativo = models.BooleanField(
        default=True,
        db_index=True
    )

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['perfil']),
            models.Index(fields=['matriz', 'perfil']),
            models.Index(fields=['matriz', 'ativo']),
        ]

    def __str__(self):
        return f'{self.username} - {self.get_perfil_display()}'

    def is_master(self):
        return self.perfil == self.PERFIL_MASTER

    def is_admin_loja(self):
        return self.perfil == self.PERFIL_ADMIN_LOJA

    def is_operador(self):
        return self.perfil == self.PERFIL_OPERADOR