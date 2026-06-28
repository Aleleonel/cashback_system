from django.db import models


class StatusOperacional(models.TextChoices):
    IMPLANTACAO = 'implantacao', 'Em implantação'
    ATIVA = 'ativa', 'Ativa'
    SUSPENSA = 'suspensa', 'Suspensa'
    BLOQUEADA = 'bloqueada', 'Bloqueada'
    ENCERRADA = 'encerrada', 'Encerrada'