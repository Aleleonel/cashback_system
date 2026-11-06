from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class StatusPedidoAtacado(models.TextChoices):
    GERADO = "GERADO", "Gerado"
    FINALIZADO = "FINALIZADO", "Finalizado"
    CANCELADO = "CANCELADO", "Cancelado"


class TipoEmissaoPedidoAtacado(models.TextChoices):
    NAO_FISCAL = "nao_fiscal", "Nao fiscal"
    FISCAL = "fiscal", "Fiscal"


class ModeloFiscalPedidoAtacado(models.TextChoices):
    NFE = "55", "NF-e"


class StatusOrcamentoAtacado(models.TextChoices):
    RASCUNHO = "RASCUNHO", "Em elaboração"
    ENVIADO = "ENVIADO", "Enviado"
    APROVADO = "APROVADO", "Aprovado"
    PEDIDO_GERADO = "PEDIDO_GERADO", "Pedido gerado"
    RECUSADO = "RECUSADO", "Recusado"
    CANCELADO = "CANCELADO", "Cancelado"
    EXPIRADO = "EXPIRADO", "Expirado"


class OrcamentoAtacado(models.Model):
    matriz = models.ForeignKey(
        "empresas.Matriz",
        on_delete=models.PROTECT,
        related_name="orcamentos_atacado",
    )
    loja = models.ForeignKey(
        "empresas.Loja",
        on_delete=models.PROTECT,
        related_name="orcamentos_atacado",
        null=True,
        blank=True,
    )
    cliente = models.ForeignKey(
        "clientes.Cliente",
        on_delete=models.PROTECT,
        related_name="orcamentos_atacado",
    )
    vendedor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="orcamentos_atacado",
        null=True,
        blank=True,
    )
    numero = models.PositiveBigIntegerField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=StatusOrcamentoAtacado.choices,
        default=StatusOrcamentoAtacado.RASCUNHO,
        db_index=True,
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    enviado_em = models.DateTimeField(null=True, blank=True)
    aprovado_em = models.DateTimeField(null=True, blank=True)
    recusado_em = models.DateTimeField(null=True, blank=True)
    cancelado_em = models.DateTimeField(null=True, blank=True)
    expirado_em = models.DateTimeField(null=True, blank=True)
    pedido_gerado_em = models.DateTimeField(null=True, blank=True)
    valido_ate = models.DateTimeField(null=True, blank=True)
    forma_pagamento = models.ForeignKey(
        "pdv.FormaPagamento", on_delete=models.PROTECT, null=True, blank=True,
        related_name="orcamentos_atacado",
    )
    parcelas = models.PositiveSmallIntegerField(default=1)
    observacoes = models.TextField(blank=True, default="")

    subtotal_produtos = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    desconto_atacado = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    ajustes_negociados = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    frete = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    total = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))

    class Meta:
        db_table = "atacado_orcamento"
        ordering = ("-id",)
        constraints = [
            models.UniqueConstraint(
                fields=("matriz", "numero"),
                condition=models.Q(numero__isnull=False),
                name="uq_atacado_orcamento_numero_matriz",
            ),
            models.CheckConstraint(
                condition=models.Q(subtotal_produtos__gte=0),
                name="ck_atacado_orc_subtotal_nao_neg",
            ),
            models.CheckConstraint(
                condition=models.Q(desconto_atacado__gte=0),
                name="ck_atacado_orc_desconto_nao_neg",
            ),
            models.CheckConstraint(
                condition=models.Q(frete__gte=0),
                name="ck_atacado_orc_frete_nao_neg",
            ),
            models.CheckConstraint(
                condition=models.Q(total__gte=0),
                name="ck_atacado_orc_total_nao_neg",
            ),
        ]

    def __str__(self):
        numero = self.numero if self.numero is not None else "rascunho"
        return f"Orçamento atacado {numero}"

    def clean(self):
        errors = {}
        if self.loja_id and self.matriz_id and self.loja.matriz_id != self.matriz_id:
            errors["loja"] = "A loja deve pertencer à mesma matriz do orçamento."
        if self.valido_ate and self.criado_em and self.valido_ate < self.criado_em:
            errors["valido_ate"] = "A validade não pode ser anterior à criação."
        if self.parcelas < 1:
            errors["parcelas"] = "Informe pelo menos uma parcela."
        if self.forma_pagamento_id:
            forma = self.forma_pagamento
            if self.matriz_id and forma.matriz_id != self.matriz_id:
                errors["forma_pagamento"] = "Forma de pagamento de outra matriz."
            elif not forma.ativa:
                errors["forma_pagamento"] = "Forma de pagamento inativa."
            elif self.parcelas > (forma.maximo_parcelas if forma.permite_parcelamento else 1):
                errors["parcelas"] = "Quantidade de parcelas nao permitida."
        elif self.parcelas != 1:
            errors["parcelas"] = "Selecione uma forma de pagamento para parcelar."
        if errors:
            raise ValidationError(errors)

    @property
    def esta_expirado(self):
        return bool(self.valido_ate and timezone.now() > self.valido_ate)

    def recalcular_totais(self, *, salvar=True):
        itens = self.itens.all()
        subtotal = sum((item.subtotal for item in itens), Decimal("0.00"))
        desconto = sum((item.desconto_atacado for item in itens), Decimal("0.00"))
        ajustes = sum((item.ajuste_negociado for item in itens), Decimal("0.00"))
        self.subtotal_produtos = subtotal
        self.desconto_atacado = desconto
        self.ajustes_negociados = ajustes
        self.total = subtotal - desconto + ajustes + self.frete
        if salvar:
            self.save(update_fields=[
                "subtotal_produtos", "desconto_atacado",
                "ajustes_negociados", "frete", "total", "atualizado_em",
            ])
        return self.total


class ItemOrcamentoAtacado(models.Model):
    orcamento = models.ForeignKey(
        OrcamentoAtacado,
        on_delete=models.CASCADE,
        related_name="itens",
    )
    produto = models.ForeignKey(
        "produtos.Produto",
        on_delete=models.PROTECT,
        related_name="itens_orcamento_atacado",
    )
    quantidade = models.DecimalField(max_digits=12, decimal_places=3)
    preco_unitario_original = models.DecimalField(max_digits=14, decimal_places=2)
    preco_unitario_base = models.DecimalField(max_digits=14, decimal_places=2)
    preco_unitario_final = models.DecimalField(max_digits=14, decimal_places=2)
    percentual_desconto_atacado = models.DecimalField(max_digits=7, decimal_places=4, default=Decimal("0.0000"))
    desconto_atacado = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    ajuste_negociado = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    produto_promocional = models.BooleanField(default=False)
    atacado_elegivel = models.BooleanField(default=True)
    conta_para_enquadramento = models.BooleanField(default=True)
    justificativa_negociacao = models.TextField(blank=True, default="")

    class Meta:
        db_table = "atacado_item_orcamento"
        ordering = ("id",)
        constraints = [
            models.CheckConstraint(condition=models.Q(quantidade__gt=0), name="ck_atacado_item_qtd_pos"),
            models.CheckConstraint(condition=models.Q(preco_unitario_original__gte=0), name="ck_atacado_item_preco_orig"),
            models.CheckConstraint(condition=models.Q(preco_unitario_base__gte=0), name="ck_atacado_item_preco_base"),
            models.CheckConstraint(condition=models.Q(preco_unitario_final__gte=0), name="ck_atacado_item_preco_final"),
            models.CheckConstraint(condition=models.Q(desconto_atacado__gte=0), name="ck_atacado_item_desc_nao_neg"),
        ]

    @property
    def subtotal(self):
        return (self.quantidade * self.preco_unitario_base).quantize(Decimal("0.01"))

    @property
    def total_final(self):
        return (self.quantidade * self.preco_unitario_final).quantize(Decimal("0.01"))


class TransicaoOrcamentoAtacado(models.Model):
    orcamento = models.ForeignKey(
        OrcamentoAtacado,
        on_delete=models.CASCADE,
        related_name="transicoes",
    )
    status_origem = models.CharField(max_length=20, choices=StatusOrcamentoAtacado.choices)
    status_destino = models.CharField(max_length=20, choices=StatusOrcamentoAtacado.choices)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="transicoes_orcamento_atacado",
    )
    ocorrido_em = models.DateTimeField(auto_now_add=True)
    observacao = models.TextField(blank=True, default="")

    class Meta:
        db_table = "atacado_transicao_orcamento"
        ordering = ("ocorrido_em", "id")


class PedidoAtacado(models.Model):
    tipo_emissao = models.CharField(
        max_length=16, choices=TipoEmissaoPedidoAtacado.choices,
        default=TipoEmissaoPedidoAtacado.NAO_FISCAL,
    )
    modelo_fiscal = models.CharField(
        max_length=2, choices=ModeloFiscalPedidoAtacado.choices, blank=True, default="",
    )
    uf_destino_fiscal = models.CharField(max_length=2, blank=True, default="")
    fiscal_solicitado_em = models.DateTimeField(null=True, blank=True)

    orcamento_origem = models.OneToOneField("atacado.OrcamentoAtacado", on_delete=models.PROTECT, related_name="pedido_atacado")
    matriz = models.ForeignKey("empresas.Matriz", on_delete=models.PROTECT, related_name="pedidos_atacado")
    loja = models.ForeignKey("empresas.Loja", on_delete=models.PROTECT, null=True, blank=True, related_name="pedidos_atacado")
    cliente = models.ForeignKey("clientes.Cliente", on_delete=models.PROTECT, related_name="pedidos_atacado")
    vendedor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name="pedidos_atacado")
    status = models.CharField(max_length=20, choices=StatusPedidoAtacado.choices, default=StatusPedidoAtacado.GERADO, db_index=True)
    finalizado_em = models.DateTimeField(null=True, blank=True)
    cancelado_em = models.DateTimeField(null=True, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    subtotal_produtos = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    desconto_atacado = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    ajustes_negociados = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    frete = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    percentual_desconto_snapshot = models.DecimalField(max_digits=7, decimal_places=2, default=0)
    produto_promocional_conta_para_faixa_snapshot = models.BooleanField(default=False)
    observacoes_snapshot = models.TextField(blank=True, default="")

class ItemPedidoAtacado(models.Model):
    pedido = models.ForeignKey(PedidoAtacado, on_delete=models.CASCADE, related_name="itens")
    produto = models.ForeignKey("produtos.Produto", on_delete=models.PROTECT)
    quantidade = models.DecimalField(max_digits=14, decimal_places=3)
    preco_unitario_original = models.DecimalField(max_digits=14, decimal_places=2)
    preco_unitario_base = models.DecimalField(max_digits=14, decimal_places=2)
    preco_unitario_final = models.DecimalField(max_digits=14, decimal_places=2)
    percentual_desconto = models.DecimalField(max_digits=7, decimal_places=2, default=0)
    desconto_atacado = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    ajuste_negociado = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    produto_promocional_snapshot = models.BooleanField(default=False)
    atacado_elegivel_snapshot = models.BooleanField(default=True)
    conta_para_enquadramento_snapshot = models.BooleanField(default=True)
    justificativa_negociacao_snapshot = models.TextField(blank=True, default="")
