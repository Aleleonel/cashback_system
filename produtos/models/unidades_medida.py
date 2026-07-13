from django.db import models

from empresas.models import Matriz


class UnidadeMedida(models.Model):
    matriz = models.ForeignKey(
        Matriz,
        on_delete=models.CASCADE,
        related_name='unidades_medida_produtos'
    )

    sigla = models.CharField(
        max_length=10
    )

    descricao = models.CharField(
        max_length=100
    )

    ativa = models.BooleanField(
        default=True,
        db_index=True
    )

    criada_em = models.DateTimeField(
        auto_now_add=True
    )

    atualizada_em = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ['sigla']
        constraints = [
            models.UniqueConstraint(
                fields=['matriz', 'sigla'],
                name='uq_unidade_produto_matriz_sigla'
            )
        ]
        indexes = [
            models.Index(
                fields=['matriz', 'sigla'],
                name='prod_unid_matriz_sigla_idx'
            ),
            models.Index(
                fields=['matriz', 'ativa'],
                name='prod_unid_matriz_ativa_idx'
            ),
        ]

    def save(self, *args, **kwargs):
        self.sigla = (self.sigla or '').strip().upper()
        self.descricao = (self.descricao or '').strip()

        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.sigla} - {self.descricao}'
