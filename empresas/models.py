from django.db import models


class Matriz(models.Model):
    nome = models.CharField(max_length=150)
    cnpj = models.CharField(max_length=18, blank=True, null=True)
    ativa = models.BooleanField(default=True)
    criada_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nome


class Loja(models.Model):
    matriz = models.ForeignKey(
        Matriz,
        on_delete=models.CASCADE,
        related_name='lojas'
    )
    nome = models.CharField(max_length=150)
    cnpj = models.CharField(max_length=18, blank=True, null=True)
    telefone = models.CharField(max_length=20, blank=True, null=True)
    ativa = models.BooleanField(default=True)
    criada_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.nome} - {self.matriz.nome}'