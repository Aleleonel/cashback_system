from django.db import models


class StatusFornecedor(models.TextChoices):
    ATIVO = 'ativo', 'Ativo'
    INATIVO = 'inativo', 'Inativo'
    BLOQUEADO = 'bloqueado', 'Bloqueado'