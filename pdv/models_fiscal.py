from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q

from pdv.choices import StatusOperacaoVenda


ZERO_MOEDA = Decimal("0.00")


class VendaFiscal(models.Model):
    venda = models.OneToOneField(
        "pdv.Venda",
        on_delete=models.PROTECT,
        related_name="fiscal",
    )

    configuracao_fiscal_id_original = models.PositiveBigIntegerField(
        blank=True,
        null=True,
    )

    regime_tributario = models.CharField(max_length=30)
    uf_origem = models.CharField(max_length=2)
    uf_destino = models.CharField(max_length=2)
    tipo_operacao = models.CharField(max_length=20)
    finalidade_operacao = models.CharField(max_length=30)
    contribuinte_icms = models.BooleanField(default=False)
    consumidor_final = models.BooleanField(default=True)

    total_base_operacao = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=ZERO_MOEDA,
    )
    total_base_icms = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=ZERO_MOEDA,
    )
    total_icms = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=ZERO_MOEDA,
    )
    total_fcp = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=ZERO_MOEDA,
    )
    total_base_pis = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=ZERO_MOEDA,
    )
    total_pis = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=ZERO_MOEDA,
    )
    total_base_cofins = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=ZERO_MOEDA,
    )
    total_cofins = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=ZERO_MOEDA,
    )
    total_base_ipi = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=ZERO_MOEDA,
    )
    total_ipi = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=ZERO_MOEDA,
    )
    total_tributos = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=ZERO_MOEDA,
    )

    resolvida_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "pdv_venda_fiscal"
        verbose_name = "Snapshot fiscal da venda"
        verbose_name_plural = "Snapshots fiscais das vendas"
        constraints = [
            models.CheckConstraint(
                condition=Q(total_base_operacao__gte=0),
                name="ck_pdv_vf_base_oper_nao_neg",
            ),
            models.CheckConstraint(
                condition=Q(total_base_icms__gte=0),
                name="ck_pdv_vf_base_icms_nao_neg",
            ),
            models.CheckConstraint(
                condition=Q(total_icms__gte=0),
                name="ck_pdv_vf_icms_nao_neg",
            ),
            models.CheckConstraint(
                condition=Q(total_fcp__gte=0),
                name="ck_pdv_vf_fcp_nao_neg",
            ),
            models.CheckConstraint(
                condition=Q(total_base_pis__gte=0),
                name="ck_pdv_vf_base_pis_nao_neg",
            ),
            models.CheckConstraint(
                condition=Q(total_pis__gte=0),
                name="ck_pdv_vf_pis_nao_neg",
            ),
            models.CheckConstraint(
                condition=Q(total_base_cofins__gte=0),
                name="ck_pdv_vf_base_cof_nao_neg",
            ),
            models.CheckConstraint(
                condition=Q(total_cofins__gte=0),
                name="ck_pdv_vf_cofins_nao_neg",
            ),
            models.CheckConstraint(
                condition=Q(total_base_ipi__gte=0),
                name="ck_pdv_vf_base_ipi_nao_neg",
            ),
            models.CheckConstraint(
                condition=Q(total_ipi__gte=0),
                name="ck_pdv_vf_ipi_nao_neg",
            ),
            models.CheckConstraint(
                condition=Q(total_tributos__gte=0),
                name="ck_pdv_vf_tributos_nao_neg",
            ),
        ]

    def __str__(self):
        return f"Fiscal da venda {self.venda_id}"

    def _validar_mutabilidade(self):
        if not self.pk:
            return

        status = (
            type(self)
            .objects
            .filter(pk=self.pk)
            .values_list("venda__status", flat=True)
            .first()
        )

        if status in {
            StatusOperacaoVenda.FINALIZADA,
            StatusOperacaoVenda.CANCELADA,
        }:
            raise ValidationError(
                "O snapshot fiscal de uma venda encerrada e imutavel."
            )

    def save(self, *args, **kwargs):
        self._validar_mutabilidade()
        self.full_clean()
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.venda.status in {
            StatusOperacaoVenda.FINALIZADA,
            StatusOperacaoVenda.CANCELADA,
        }:
            raise ValidationError(
                "O snapshot fiscal de uma venda encerrada nao pode ser excluido."
            )
        return super().delete(*args, **kwargs)


class ItemVendaFiscal(models.Model):
    item_venda = models.OneToOneField(
        "pdv.ItemVenda",
        on_delete=models.PROTECT,
        related_name="fiscal",
    )

    regra_fiscal_id_original = models.PositiveBigIntegerField(
        blank=True,
        null=True,
    )
    configuracao_fiscal_id_original = models.PositiveBigIntegerField(
        blank=True,
        null=True,
    )

    origem_mercadoria_codigo = models.CharField(
        max_length=2,
        blank=True,
    )
    ncm_codigo = models.CharField(
        max_length=16,
        blank=True,
        db_index=True,
    )
    ncm_descricao = models.CharField(
        max_length=300,
        blank=True,
    )
    cest_codigo = models.CharField(
        max_length=16,
        blank=True,
    )
    cfop_codigo = models.CharField(
        max_length=8,
        blank=True,
        db_index=True,
    )
    cfop_descricao = models.CharField(
        max_length=300,
        blank=True,
    )

    cst_icms_codigo = models.CharField(max_length=4, blank=True)
    csosn_codigo = models.CharField(max_length=4, blank=True)
    cst_pis_codigo = models.CharField(max_length=4, blank=True)
    cst_cofins_codigo = models.CharField(max_length=4, blank=True)
    cst_ipi_codigo = models.CharField(max_length=4, blank=True)

    beneficio_fiscal_codigo = models.CharField(
        max_length=60,
        blank=True,
    )
    beneficio_fiscal_descricao = models.CharField(
        max_length=300,
        blank=True,
    )
    regra_fiscal_codigo = models.CharField(
        max_length=80,
        blank=True,
        db_index=True,
    )
    regra_fiscal_descricao = models.CharField(
        max_length=300,
        blank=True,
    )

    regime_tributario = models.CharField(max_length=30)
    uf_origem = models.CharField(max_length=2)
    uf_destino = models.CharField(max_length=2)
    tipo_operacao = models.CharField(max_length=20)
    finalidade_operacao = models.CharField(max_length=30)
    contribuinte_icms = models.BooleanField(default=False)
    consumidor_final = models.BooleanField(default=True)

    quantidade = models.DecimalField(
        max_digits=14,
        decimal_places=3,
    )
    valor_unitario = models.DecimalField(
        max_digits=14,
        decimal_places=2,
    )
    valor_produtos = models.DecimalField(
        max_digits=14,
        decimal_places=2,
    )
    desconto = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=ZERO_MOEDA,
    )
    acrescimo = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=ZERO_MOEDA,
    )
    frete = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=ZERO_MOEDA,
    )
    seguro = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=ZERO_MOEDA,
    )
    outras_despesas = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=ZERO_MOEDA,
    )
    base_operacao = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=ZERO_MOEDA,
    )

    base_icms = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=ZERO_MOEDA,
    )
    aliquota_icms = models.DecimalField(
        max_digits=9,
        decimal_places=4,
        blank=True,
        null=True,
    )
    percentual_reducao_base_icms = models.DecimalField(
        max_digits=9,
        decimal_places=4,
        default=ZERO_MOEDA,
    )
    valor_icms_bruto = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=ZERO_MOEDA,
    )
    percentual_diferimento_icms = models.DecimalField(
        max_digits=9,
        decimal_places=4,
        default=ZERO_MOEDA,
    )
    valor_icms_diferido = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=ZERO_MOEDA,
    )
    valor_icms = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=ZERO_MOEDA,
    )

    base_fcp = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=ZERO_MOEDA,
    )
    aliquota_fcp = models.DecimalField(
        max_digits=9,
        decimal_places=4,
        blank=True,
        null=True,
    )
    valor_fcp = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=ZERO_MOEDA,
    )

    base_pis = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=ZERO_MOEDA,
    )
    aliquota_pis = models.DecimalField(
        max_digits=9,
        decimal_places=4,
        blank=True,
        null=True,
    )
    valor_pis = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=ZERO_MOEDA,
    )

    base_cofins = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=ZERO_MOEDA,
    )
    aliquota_cofins = models.DecimalField(
        max_digits=9,
        decimal_places=4,
        blank=True,
        null=True,
    )
    valor_cofins = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=ZERO_MOEDA,
    )

    base_ipi = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=ZERO_MOEDA,
    )
    aliquota_ipi = models.DecimalField(
        max_digits=9,
        decimal_places=4,
        blank=True,
        null=True,
    )
    valor_ipi = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=ZERO_MOEDA,
    )

    valor_total_tributos = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=ZERO_MOEDA,
    )

    resolvido_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "pdv_item_venda_fiscal"
        verbose_name = "Snapshot fiscal do item da venda"
        verbose_name_plural = "Snapshots fiscais dos itens da venda"
        constraints = [
            models.CheckConstraint(
                condition=Q(quantidade__gt=0),
                name="ck_pdv_ivf_qtd_positiva",
            ),
            models.CheckConstraint(
                condition=Q(valor_unitario__gte=0),
                name="ck_pdv_ivf_unit_nao_neg",
            ),
            models.CheckConstraint(
                condition=Q(valor_produtos__gte=0),
                name="ck_pdv_ivf_prod_nao_neg",
            ),
            models.CheckConstraint(
                condition=Q(desconto__gte=0),
                name="ck_pdv_ivf_desc_nao_neg",
            ),
            models.CheckConstraint(
                condition=Q(acrescimo__gte=0),
                name="ck_pdv_ivf_acr_nao_neg",
            ),
            models.CheckConstraint(
                condition=Q(frete__gte=0),
                name="ck_pdv_ivf_frete_nao_neg",
            ),
            models.CheckConstraint(
                condition=Q(seguro__gte=0),
                name="ck_pdv_ivf_seguro_nao_neg",
            ),
            models.CheckConstraint(
                condition=Q(outras_despesas__gte=0),
                name="ck_pdv_ivf_outras_nao_neg",
            ),
            models.CheckConstraint(
                condition=Q(base_operacao__gte=0),
                name="ck_pdv_ivf_baseop_nao_neg",
            ),
            models.CheckConstraint(
                condition=Q(base_icms__gte=0),
                name="ck_pdv_ivf_bicms_nao_neg",
            ),
            models.CheckConstraint(
                condition=Q(valor_icms__gte=0),
                name="ck_pdv_ivf_icms_nao_neg",
            ),
            models.CheckConstraint(
                condition=Q(base_fcp__gte=0),
                name="ck_pdv_ivf_bfcp_nao_neg",
            ),
            models.CheckConstraint(
                condition=Q(valor_fcp__gte=0),
                name="ck_pdv_ivf_fcp_nao_neg",
            ),
            models.CheckConstraint(
                condition=Q(base_pis__gte=0),
                name="ck_pdv_ivf_bpis_nao_neg",
            ),
            models.CheckConstraint(
                condition=Q(valor_pis__gte=0),
                name="ck_pdv_ivf_pis_nao_neg",
            ),
            models.CheckConstraint(
                condition=Q(base_cofins__gte=0),
                name="ck_pdv_ivf_bcof_nao_neg",
            ),
            models.CheckConstraint(
                condition=Q(valor_cofins__gte=0),
                name="ck_pdv_ivf_cof_nao_neg",
            ),
            models.CheckConstraint(
                condition=Q(base_ipi__gte=0),
                name="ck_pdv_ivf_bipi_nao_neg",
            ),
            models.CheckConstraint(
                condition=Q(valor_ipi__gte=0),
                name="ck_pdv_ivf_ipi_nao_neg",
            ),
            models.CheckConstraint(
                condition=Q(valor_total_tributos__gte=0),
                name="ck_pdv_ivf_tottrib_nao_neg",
            ),
            models.CheckConstraint(
                condition=Q(percentual_reducao_base_icms__gte=0)
                & Q(percentual_reducao_base_icms__lte=100),
                name="ck_pdv_ivf_reducao_0_100",
            ),
            models.CheckConstraint(
                condition=Q(percentual_diferimento_icms__gte=0)
                & Q(percentual_diferimento_icms__lte=100),
                name="ck_pdv_ivf_difer_0_100",
            ),
        ]

    def __str__(self):
        return f"Fiscal do item {self.item_venda_id}"

    def _status_venda(self):
        return (
            type(self)
            .objects
            .filter(pk=self.pk)
            .values_list("item_venda__venda__status", flat=True)
            .first()
        )

    def _validar_mutabilidade(self):
        if not self.pk:
            return

        if self._status_venda() in {
            StatusOperacaoVenda.FINALIZADA,
            StatusOperacaoVenda.CANCELADA,
        }:
            raise ValidationError(
                "O snapshot fiscal de um item de venda encerrada e imutavel."
            )

    def save(self, *args, **kwargs):
        self._validar_mutabilidade()
        self.full_clean()
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.item_venda.venda.status in {
            StatusOperacaoVenda.FINALIZADA,
            StatusOperacaoVenda.CANCELADA,
        }:
            raise ValidationError(
                "O snapshot fiscal de um item de venda encerrada nao pode ser excluido."
            )
        return super().delete(*args, **kwargs)