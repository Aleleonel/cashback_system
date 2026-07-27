from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models


class ConfiguracaoComercial(models.Model):
    matriz = models.OneToOneField(
        "empresas.Matriz",
        on_delete=models.CASCADE,
        related_name="configuracao_comercial",
    )

    atacado_ativo = models.BooleanField(default=False)
    pedido_minimo_atacado = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    desconto_atacado_percentual = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    cashback_ativo = models.BooleanField(default=True)
    voucher_ativo = models.BooleanField(default=True)
    promocoes_ativas = models.BooleanField(default=True)
    brindes_ativos = models.BooleanField(default=True)
    arredondamento_ativo = models.BooleanField(default=False)

    criada_em = models.DateTimeField(auto_now_add=True)
    atualizada_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "configuracao comercial"
        verbose_name_plural = "configuracoes comerciais"
        ordering = ("matriz_id",)

    def __str__(self):
        return f"Regras comerciais - {self.matriz}"

    def clean(self):
        erros = {}

        if self.pedido_minimo_atacado < 0:
            erros["pedido_minimo_atacado"] = (
                "O pedido minimo do atacado nao pode ser negativo."
            )

        if not 0 <= self.desconto_atacado_percentual <= 100:
            erros["desconto_atacado_percentual"] = (
                "O desconto do atacado deve estar entre 0 e 100."
            )

        if erros:
            raise ValidationError(erros)
