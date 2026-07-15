from django.db import models

from empresas.models import Matriz


class Categoria(models.Model):
    matriz = models.ForeignKey(
        Matriz,
        on_delete=models.CASCADE,
        related_name='categorias_produtos'
    )

    nome = models.CharField(
        max_length=100
    )

    descricao = models.TextField(
        blank=True
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
        ordering = ['nome']
        constraints = [
            models.UniqueConstraint(
                fields=['matriz', 'nome'],
                name='uq_categoria_produto_matriz_nome'
            )
        ]
        indexes = [
            models.Index(
                fields=['matriz', 'nome'],
                name='prod_cat_matriz_nome_idx'
            ),
            models.Index(
                fields=['matriz', 'ativa'],
                name='prod_cat_matriz_ativa_idx'
            ),
        ]

    def __str__(self):
        return self.nome
