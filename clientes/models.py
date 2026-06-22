from django.db import models
from empresas.models import Matriz, Loja

from decimal import Decimal


class Cliente(models.Model):

    matriz = models.ForeignKey(
        Matriz,
        on_delete=models.CASCADE,
        related_name='clientes'
    )

    loja_cadastro = models.ForeignKey(
        Loja,
        on_delete=models.CASCADE,
        related_name='clientes_cadastrados',
        null=True,
        blank=True
    )

    nome = models.CharField(max_length=150)
    cpf = models.CharField(max_length=14)
    telefone = models.CharField(max_length=20, blank=True, null=True)
    data_nascimento = models.DateField(blank=True, null=True)
    email = models.EmailField(blank=True, null=True)

    aceita_email = models.BooleanField(default=True)
    aceita_sms = models.BooleanField(default=False)

    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('matriz', 'cpf')
        ordering = ['nome']

    def __str__(self):
        return f'{self.nome} - {self.cpf}'

    