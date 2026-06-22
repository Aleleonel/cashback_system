from django.contrib.auth.models import AbstractUser
from django.db import models

from empresas.models import Matriz, Loja


class Usuario(AbstractUser):

    PERFIL_CHOICES = [
        ('master', 'Master'),
        ('admin_loja', 'Administrador da Loja'),
        ('operador', 'Operador'),
    ]

    perfil = models.CharField(
        max_length=20,
        choices=PERFIL_CHOICES,
        default='operador'
    )

    matriz = models.ForeignKey(
        Matriz,
        on_delete=models.SET_NULL,
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
        null=True
    )

    ativo = models.BooleanField(default=True)

    def __str__(self):
        return f'{self.username} - {self.get_perfil_display()}'

    def is_master(self):
        return self.perfil == 'master'

    def is_admin_loja(self):
        return self.perfil == 'admin_loja'

    def is_operador(self):
        return self.perfil == 'operador'