from django.db import models


class StatusProduto(models.TextChoices):
    ATIVO = 'ativo', 'Ativo'
    INATIVO = 'inativo', 'Inativo'
    DESCONTINUADO = 'descontinuado', 'Descontinuado'


class OrigemPreco(models.TextChoices):
    MANUAL = 'manual', 'Manual'
    FORMACAO_PRECO = 'formacao_preco', 'Formação de preço'
