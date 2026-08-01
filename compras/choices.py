from django.db import models


class StatusFornecedor(models.TextChoices):
    ATIVO = 'ativo', 'Ativo'
    INATIVO = 'inativo', 'Inativo'
    BLOQUEADO = 'bloqueado', 'Bloqueado'


class StatusPedidoCompra(models.TextChoices):
    RASCUNHO = 'rascunho', 'Rascunho'
    ENVIADO = 'enviado', 'Enviado ao fornecedor'
    PARCIAL = 'parcial', 'Recebido parcialmente'
    RECEBIDO = 'recebido', 'Recebido'
    CANCELADO = 'cancelado', 'Cancelado'