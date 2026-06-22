from django.db import models
from empresas.models import Loja


class Cliente(models.Model):
    loja = models.ForeignKey(
        Loja,
        on_delete=models.CASCADE,
        related_name='clientes'
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
        unique_together = ('loja', 'cpf')
        ordering = ['nome']

    def __str__(self):
        return f'{self.nome} - {self.cpf}'