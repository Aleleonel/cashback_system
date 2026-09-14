import uuid

from django.db import models
from django.db.models import Q


class TituloFinanceiro(models.Model):
    class Natureza(models.TextChoices):
        PAGAR = "PAGAR", "Pagar"
        RECEBER = "RECEBER", "Receber"

    class OrigemTipo(models.TextChoices):
        COMPRA_RECEBIMENTO = "COMPRA_RECEBIMENTO", "Compra - recebimento"
        VENDA_PAGAMENTO = "VENDA_PAGAMENTO", "Venda - pagamento"
        MANUAL = "MANUAL", "Manual"
        AJUSTE = "AJUSTE", "Ajuste"
    class Status(models.TextChoices):
        ABERTO = "ABERTO", "Aberto"
        PARCIAL = "PARCIAL", "Parcial"
        LIQUIDADO = "LIQUIDADO", "Liquidado"
        CANCELADO = "CANCELADO", "Cancelado"

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    matriz = models.ForeignKey(
        "empresas.Matriz",
        on_delete=models.PROTECT,
        related_name="titulos_financeiros",
    )
    loja = models.ForeignKey(
        "empresas.Loja",
        on_delete=models.PROTECT,
        related_name="titulos_financeiros",
        null=True,
        blank=True,
    )
    natureza = models.CharField(max_length=10, choices=Natureza.choices)
    origem_tipo = models.CharField(max_length=40, choices=OrigemTipo.choices)
    origem_id = models.CharField(max_length=100)
    chave_idempotencia = models.CharField(max_length=150)
    descricao = models.CharField(max_length=255)
    valor_original = models.DecimalField(max_digits=14, decimal_places=2)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.ABERTO)
    data_emissao = models.DateField()
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["matriz", "chave_idempotencia"],
                name="uq_fin_titulo_matriz_idempotencia",
            ),
            models.UniqueConstraint(
                fields=["matriz", "natureza", "origem_tipo", "origem_id"],
                name="uq_fin_titulo_matriz_natureza_origem",
            ),
            models.CheckConstraint(
                condition=Q(valor_original__gt=0),
                name="ck_fin_titulo_valor_positivo",
            ),
        ]
        indexes = [
            models.Index(fields=["matriz", "natureza", "status"], name="ix_fin_tit_mat_nat_st"),
            models.Index(fields=["matriz", "loja", "status"], name="ix_fin_tit_mat_loja_st"),
            models.Index(fields=["origem_tipo", "origem_id"], name="ix_fin_tit_origem"),
        ]


class ParcelaFinanceira(models.Model):
    class OrigemTipo(models.TextChoices):
        COMPRA_RECEBIMENTO = "COMPRA_RECEBIMENTO", "Compra - recebimento"
        VENDA_PAGAMENTO = "VENDA_PAGAMENTO", "Venda - pagamento"
        MANUAL = "MANUAL", "Manual"
        AJUSTE = "AJUSTE", "Ajuste"
    class Status(models.TextChoices):
        ABERTO = "ABERTO", "Aberta"
        PARCIAL = "PARCIAL", "Parcial"
        LIQUIDADO = "LIQUIDADO", "Liquidada"
        CANCELADO = "CANCELADO", "Cancelada"

    titulo = models.ForeignKey(
        TituloFinanceiro,
        on_delete=models.PROTECT,
        related_name="parcelas",
    )
    numero = models.PositiveSmallIntegerField()
    vencimento = models.DateField()
    valor_original = models.DecimalField(max_digits=14, decimal_places=2)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.ABERTO)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["titulo", "numero"],
                name="uq_fin_parcela_titulo_numero",
            ),
            models.CheckConstraint(
                condition=Q(numero__gt=0),
                name="ck_fin_parcela_numero_positivo",
            ),
            models.CheckConstraint(
                condition=Q(valor_original__gt=0),
                name="ck_fin_parcela_valor_positivo",
            ),
        ]
        indexes = [
            models.Index(fields=["vencimento", "status"], name="ix_fin_parc_venc_st"),
            models.Index(fields=["titulo", "status"], name="ix_fin_parc_tit_st"),
        ]


class BaixaFinanceira(models.Model):
    class Tipo(models.TextChoices):
        BAIXA = "BAIXA", "Baixa"
        ESTORNO = "ESTORNO", "Estorno"

    parcela = models.ForeignKey(
        ParcelaFinanceira,
        on_delete=models.PROTECT,
        related_name="baixas",
    )
    valor = models.DecimalField(max_digits=14, decimal_places=2)
    data = models.DateField()
    tipo = models.CharField(max_length=10, choices=Tipo.choices)
    chave_idempotencia = models.CharField(max_length=150)
    observacao = models.TextField(blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["parcela", "chave_idempotencia"],
                name="uq_fin_baixa_parcela_idempotencia",
            ),
            models.CheckConstraint(
                condition=Q(valor__gt=0),
                name="ck_fin_baixa_valor_positivo",
            ),
        ]
        indexes = [
            models.Index(fields=["parcela", "data"], name="ix_fin_baixa_parc_data"),
        ]