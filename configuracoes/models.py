from decimal import Decimal

from django.conf import settings
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

class ConfiguracaoComissaoMatriz(models.Model):
    matriz = models.OneToOneField(
        "empresas.Matriz", on_delete=models.CASCADE, related_name="configuracao_comissao",
    )
    exigir_minimo_individual = models.BooleanField(default=False)
    minimo_vendas_vendedor = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    criada_em = models.DateTimeField(auto_now_add=True)
    atualizada_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "ConfiguraÃ§Ã£o de comissÃ£o da matriz"
        verbose_name_plural = "ConfiguraÃ§Ãµes de comissÃ£o das matrizes"
        constraints = [
            models.CheckConstraint(condition=models.Q(minimo_vendas_vendedor__gte=0), name="ck_cfg_comissao_minimo_nao_negativo"),
        ]

    def __str__(self):
        return f"ComissÃµes - {self.matriz}"


class MetaComissaoLoja(models.Model):
    loja = models.ForeignKey("empresas.Loja", on_delete=models.CASCADE, related_name="metas_comissao")
    valor_meta = models.DecimalField(max_digits=14, decimal_places=2)
    percentual_comissao = models.DecimalField(max_digits=7, decimal_places=4)
    ativa = models.BooleanField(default=True)
    criada_em = models.DateTimeField(auto_now_add=True)
    atualizada_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["valor_meta", "pk"]
        verbose_name = "Meta de comissÃ£o da loja"
        verbose_name_plural = "Metas de comissÃ£o das lojas"
        constraints = [
            models.UniqueConstraint(fields=["loja", "valor_meta"], name="uq_meta_comissao_loja_valor"),
            models.CheckConstraint(condition=models.Q(valor_meta__gte=0), name="ck_meta_comissao_valor_nao_negativo"),
            models.CheckConstraint(condition=models.Q(percentual_comissao__gte=0), name="ck_meta_comissao_percentual_nao_negativo"),
        ]

    def __str__(self):
        return f"{self.loja} - {self.valor_meta} - {self.percentual_comissao}%"


class FechamentoComissao(models.Model):
    matriz = models.ForeignKey("empresas.Matriz", on_delete=models.PROTECT, related_name="fechamentos_comissao")
    loja = models.ForeignKey("empresas.Loja", on_delete=models.PROTECT, related_name="fechamentos_comissao")
    competencia_ano = models.PositiveSmallIntegerField()
    competencia_mes = models.PositiveSmallIntegerField()
    total_vendas_loja = models.DecimalField(max_digits=14, decimal_places=2)
    valor_meta_atingida = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    percentual_aplicado = models.DecimalField(max_digits=7, decimal_places=4)
    exigir_minimo_individual = models.BooleanField(default=False)
    minimo_individual = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    fechado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-competencia_ano", "-competencia_mes", "loja_id"]
        constraints = [
            models.UniqueConstraint(fields=["loja", "competencia_ano", "competencia_mes"], name="uq_fech_comissao_loja_comp"),
            models.CheckConstraint(condition=models.Q(competencia_mes__gte=1) & models.Q(competencia_mes__lte=12), name="ck_fech_comissao_mes_1_12"),
            models.CheckConstraint(condition=models.Q(total_vendas_loja__gte=0), name="ck_fech_comissao_total_nao_neg"),
            models.CheckConstraint(condition=models.Q(percentual_aplicado__gte=0), name="ck_fech_comissao_pct_nao_neg"),
            models.CheckConstraint(condition=models.Q(minimo_individual__gte=0), name="ck_fech_comissao_min_nao_neg"),
        ]

    def _validar_mutabilidade(self):
        if self.pk and type(self).objects.filter(pk=self.pk).exists():
            raise ValidationError("O fechamento de comissao mensal e imutavel.")

    def clean(self):
        super().clean()
        if self.loja_id and self.matriz_id and self.loja.matriz_id != self.matriz_id:
            raise ValidationError({
                "loja": "A loja do fechamento deve pertencer \u00e0 matriz informada."
            })

    def save(self, *args, **kwargs):
        self._validar_mutabilidade()
        self.full_clean()
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.pk:
            raise ValidationError("O fechamento de comissao mensal nao pode ser excluido.")
        return super().delete(*args, **kwargs)


class ComissaoVendedor(models.Model):
    fechamento = models.ForeignKey(FechamentoComissao, on_delete=models.PROTECT, related_name="comissoes_vendedores")
    vendedor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="comissoes_historicas")
    vendedor_uuid_original = models.UUIDField()
    vendedor_nome_original = models.CharField(max_length=300)
    total_vendas_vendedor = models.DecimalField(max_digits=14, decimal_places=2)
    elegivel = models.BooleanField(default=True)
    valor_comissao = models.DecimalField(max_digits=14, decimal_places=2)
    criada_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["fechamento_id", "vendedor_id"]
        constraints = [
            models.UniqueConstraint(fields=["fechamento", "vendedor"], name="uq_comissao_fech_vendedor"),
            models.CheckConstraint(condition=models.Q(total_vendas_vendedor__gte=0), name="ck_comissao_vend_total_nao_neg"),
            models.CheckConstraint(condition=models.Q(valor_comissao__gte=0), name="ck_comissao_vend_valor_nao_neg"),
        ]

    def _validar_mutabilidade(self):
        if self.pk and type(self).objects.filter(pk=self.pk).exists():
            raise ValidationError("A comissao historica do vendedor e imutavel.")

    def save(self, *args, **kwargs):
        self._validar_mutabilidade()
        self.full_clean()
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.pk:
            raise ValidationError("A comissao historica do vendedor nao pode ser excluida.")
        return super().delete(*args, **kwargs)