import uuid
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q

from clientes.models import Cliente
from empresas.models import Loja, Matriz
from produtos.models import Produto

from .choices import (
    ModalidadeComercial,
    StatusCaixa,
    StatusOperacaoVenda,
    StatusSessaoCaixa,
    TipoEmissaoVenda,
    TipoFormaPagamento,
    TipoMovimentacaoCaixa,
    TipoOperacaoVenda,
)


class Caixa(models.Model):
    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        db_index=True,
    )
    matriz = models.ForeignKey(
        Matriz,
        on_delete=models.PROTECT,
        related_name="caixas_pdv",
    )
    loja = models.ForeignKey(
        Loja,
        on_delete=models.PROTECT,
        related_name="caixas_pdv",
    )
    nome = models.CharField(max_length=100)
    codigo = models.CharField(max_length=30)
    status = models.CharField(
        max_length=20,
        choices=StatusCaixa.choices,
        default=StatusCaixa.ATIVO,
        db_index=True,
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["loja", "nome"]
        constraints = [
            models.UniqueConstraint(
                fields=["loja", "codigo"],
                name="uq_pdv_caixa_loja_codigo",
            ),
        ]
        indexes = [
            models.Index(fields=["matriz", "status"]),
            models.Index(fields=["loja", "status"]),
            models.Index(fields=["loja", "nome"]),
        ]

    def clean(self):
        errors = {}
        if self.loja_id and self.matriz_id and self.loja.matriz_id != self.matriz_id:
            errors["loja"] = "A loja deve pertencer a matriz informada."
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.nome} - {self.loja.nome}"


class SessaoCaixa(models.Model):
    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        db_index=True,
    )
    caixa = models.ForeignKey(
        Caixa,
        on_delete=models.PROTECT,
        related_name="sessoes",
    )
    operador_abertura = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="sessoes_caixa_abertas",
    )
    operador_fechamento = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="sessoes_caixa_fechadas",
        blank=True,
        null=True,
    )
    status = models.CharField(
        max_length=20,
        choices=StatusSessaoCaixa.choices,
        default=StatusSessaoCaixa.ABERTA,
        db_index=True,
    )
    valor_abertura = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    valor_fechamento_informado = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        blank=True,
        null=True,
    )
    valor_fechamento_calculado = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        blank=True,
        null=True,
    )
    diferenca_fechamento = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        blank=True,
        null=True,
    )
    aberta_em = models.DateTimeField(auto_now_add=True, db_index=True)
    fechada_em = models.DateTimeField(blank=True, null=True, db_index=True)
    observacao_abertura = models.TextField(blank=True)
    observacao_fechamento = models.TextField(blank=True)

    class Meta:
        ordering = ["-aberta_em"]
        constraints = [
            models.UniqueConstraint(
                fields=["caixa"],
                condition=Q(status=StatusSessaoCaixa.ABERTA),
                name="uq_pdv_uma_sessao_aberta_por_caixa",
            ),
            models.CheckConstraint(
                condition=Q(valor_abertura__gte=0),
                name="ck_pdv_sessao_valor_abertura_nao_negativo",
            ),
        ]
        indexes = [
            models.Index(fields=["caixa", "status"]),
            models.Index(fields=["operador_abertura", "status"]),
            models.Index(fields=["aberta_em"]),
        ]

    @property
    def esta_aberta(self):
        return self.status == StatusSessaoCaixa.ABERTA

    def __str__(self):
        return f"{self.caixa} - {self.aberta_em:%d/%m/%Y %H:%M}"


class FormaPagamento(models.Model):
    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        db_index=True,
    )
    matriz = models.ForeignKey(
        Matriz,
        on_delete=models.PROTECT,
        related_name="formas_pagamento_pdv",
    )
    nome = models.CharField(max_length=100)
    codigo = models.CharField(max_length=40)
    tipo = models.CharField(
        max_length=30,
        choices=TipoFormaPagamento.choices,
        default=TipoFormaPagamento.OUTRO,
        db_index=True,
    )
    ativa = models.BooleanField(default=True, db_index=True)
    permite_parcelamento = models.BooleanField(default=False)
    maximo_parcelas = models.PositiveSmallIntegerField(default=1)
    exige_cliente_identificado = models.BooleanField(default=False)
    exige_autorizacao = models.BooleanField(default=False)
    gera_contas_receber = models.BooleanField(default=False)
    movimenta_caixa = models.BooleanField(default=True)
    permite_troco = models.BooleanField(default=False)
    somente_funcionario = models.BooleanField(default=False)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["nome"]
        constraints = [
            models.UniqueConstraint(
                fields=["matriz", "codigo"],
                name="uq_pdv_forma_pagamento_matriz_codigo",
            ),
            models.CheckConstraint(
                condition=Q(maximo_parcelas__gte=1),
                name="ck_pdv_forma_pagamento_minimo_uma_parcela",
            ),
        ]
        indexes = [
            models.Index(fields=["matriz", "ativa"]),
            models.Index(fields=["matriz", "tipo"]),
            models.Index(fields=["matriz", "nome"]),
        ]

    def clean(self):
        errors = {}
        if not self.permite_parcelamento and self.maximo_parcelas != 1:
            errors["maximo_parcelas"] = (
                "Uma forma sem parcelamento deve possuir no maximo 1 parcela."
            )
        if self.permite_troco and self.tipo != TipoFormaPagamento.DINHEIRO:
            errors["permite_troco"] = "Somente dinheiro pode permitir troco."
        if self.somente_funcionario and not self.exige_cliente_identificado:
            errors["exige_cliente_identificado"] = (
                "Pagamento exclusivo de funcionario exige identificacao."
            )
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return self.nome


class Venda(models.Model):
    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        db_index=True,
    )
    matriz = models.ForeignKey(
        Matriz,
        on_delete=models.PROTECT,
        related_name="vendas_pdv",
    )
    loja = models.ForeignKey(
        Loja,
        on_delete=models.PROTECT,
        related_name="vendas_pdv",
    )
    sessao_caixa = models.ForeignKey(
        SessaoCaixa,
        on_delete=models.PROTECT,
        related_name="vendas",
        blank=True,
        null=True,
    )
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.PROTECT,
        related_name="vendas_pdv",
        blank=True,
        null=True,
    )
    operador = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="vendas_pdv_operadas",
    )
    vendedor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="vendas_pdv_vendidas",
        blank=True,
        null=True,
    )
    numero = models.PositiveBigIntegerField(blank=True, null=True)
    tipo_operacao = models.CharField(
        max_length=20,
        choices=TipoOperacaoVenda.choices,
        default=TipoOperacaoVenda.VENDA,
        db_index=True,
    )
    status = models.CharField(
        max_length=20,
        choices=StatusOperacaoVenda.choices,
        default=StatusOperacaoVenda.RASCUNHO,
        db_index=True,
    )
    modalidade = models.CharField(
        max_length=20,
        choices=ModalidadeComercial.choices,
        default=ModalidadeComercial.VAREJO,
        db_index=True,
    )
    tipo_emissao = models.CharField(
        max_length=20,
        choices=TipoEmissaoVenda.choices,
        default=TipoEmissaoVenda.NAO_FISCAL,
        db_index=True,
    )
    subtotal = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    desconto = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    acrescimo = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    total = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    observacao = models.TextField(blank=True)
    desconto_geral = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    acrescimo_geral = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    quantidade_itens = models.DecimalField(
        max_digits=14,
        decimal_places=3,
        default=Decimal("0.000"),
    )
    criada_em = models.DateTimeField(auto_now_add=True, db_index=True)
    atualizada_em = models.DateTimeField(auto_now=True)
    finalizada_em = models.DateTimeField(blank=True, null=True, db_index=True)
    cancelada_em = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ["-criada_em"]
        constraints = [
            models.UniqueConstraint(
                fields=["loja", "numero"],
                condition=Q(numero__isnull=False),
                name="uq_pdv_venda_loja_numero",
            ),
            models.CheckConstraint(
                condition=Q(subtotal__gte=0),
                name="ck_pdv_venda_subtotal_nao_negativo",
            ),
            models.CheckConstraint(
                condition=Q(desconto__gte=0),
                name="ck_pdv_venda_desconto_nao_negativo",
            ),
            models.CheckConstraint(
                condition=Q(acrescimo__gte=0),
                name="ck_pdv_venda_acrescimo_nao_negativo",
            ),
            models.CheckConstraint(
                condition=Q(total__gte=0),
                name="ck_pdv_venda_total_nao_negativo",
            ),
        ]
        indexes = [
            models.Index(fields=["matriz", "status"]),
            models.Index(fields=["loja", "status"]),
            models.Index(fields=["sessao_caixa", "status"]),
            models.Index(fields=["cliente", "criada_em"]),
            models.Index(fields=["operador", "criada_em"]),
            models.Index(fields=["tipo_operacao", "status"]),
        ]

    def clean(self):
        errors = {}
        if self.loja_id and self.matriz_id and self.loja.matriz_id != self.matriz_id:
            errors["loja"] = "A loja deve pertencer a matriz informada."

        if self.cliente_id and self.cliente.matriz_id != self.matriz_id:
            errors["cliente"] = "O cliente deve pertencer a mesma matriz da venda."

        if self.sessao_caixa_id:
            if self.sessao_caixa.caixa.loja_id != self.loja_id:
                errors["sessao_caixa"] = "A sessao deve pertencer a loja da venda."

        if self.status == StatusOperacaoVenda.FINALIZADA:
            if not self.cliente_id:
                errors["cliente"] = (
                    "Uma venda finalizada deve possuir cliente identificado "
                    "ou o cliente padrao CONSUMIDOR."
                )
            if self.tipo_operacao == TipoOperacaoVenda.VENDA and not self.sessao_caixa_id:
                errors["sessao_caixa"] = (
                    "Uma venda finalizada deve estar vinculada a uma sessao de caixa."
                )
            if not self.vendedor_id:
                errors["vendedor"] = (
                    "Uma venda finalizada deve estar vinculada a um vendedor."
                )

        total_calculado = self.subtotal - self.desconto + self.acrescimo
        if self.total != total_calculado:
            errors["total"] = (
                "O total deve ser igual ao subtotal menos desconto mais acrescimo."
            )

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        numero = self.numero if self.numero is not None else "rascunho"
        return f"Venda {numero} - {self.loja.nome}"



    def recalcular_totais(self, *, salvar=True):
        itens = self.itens.filter(cancelado=False)
        subtotal = Decimal("0.00")
        desconto_itens = Decimal("0.00")
        acrescimo_itens = Decimal("0.00")
        quantidade = Decimal("0.000")

        for item in itens:
            subtotal += item.subtotal
            desconto_itens += item.desconto
            acrescimo_itens += item.acrescimo
            quantidade += item.quantidade

        self.subtotal = subtotal.quantize(Decimal("0.01"))
        self.desconto = (desconto_itens + self.desconto_geral).quantize(Decimal("0.01"))
        self.acrescimo = (acrescimo_itens + self.acrescimo_geral).quantize(Decimal("0.01"))
        self.total = (self.subtotal - self.desconto + self.acrescimo).quantize(Decimal("0.01"))
        self.quantidade_itens = quantidade.quantize(Decimal("0.001"))

        if self.total < Decimal("0.00"):
            raise ValidationError({"total": "O total da venda nao pode ser negativo."})

        if salvar and self.pk:
            self.save(update_fields=[
                "subtotal", "desconto", "acrescimo", "total", "quantidade_itens"
            ])
        return self.total


class ItemVenda(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    venda = models.ForeignKey(Venda, on_delete=models.PROTECT, related_name="itens")
    produto = models.ForeignKey(Produto, on_delete=models.PROTECT, related_name="itens_venda_pdv")
    sequencia = models.PositiveIntegerField()
    quantidade = models.DecimalField(max_digits=14, decimal_places=3, default=Decimal("1.000"))
    preco_unitario = models.DecimalField(max_digits=14, decimal_places=2)
    desconto = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    acrescimo = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    subtotal = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    total = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    observacao = models.TextField(blank=True)
    cancelado = models.BooleanField(default=False, db_index=True)
    motivo_cancelamento = models.CharField(max_length=255, blank=True)
    cancelado_em = models.DateTimeField(blank=True, null=True)
    cancelado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="itens_venda_cancelados",
        blank=True,
        null=True,
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["venda", "sequencia"]
        constraints = [
            models.UniqueConstraint(fields=["venda", "sequencia"], name="uq_pdv_item_venda_sequencia"),
            models.CheckConstraint(condition=Q(quantidade__gt=0), name="ck_pdv_item_venda_quantidade_positiva"),
            models.CheckConstraint(condition=Q(preco_unitario__gte=0), name="ck_pdv_item_venda_preco_nao_negativo"),
            models.CheckConstraint(condition=Q(desconto__gte=0), name="ck_pdv_item_venda_desconto_nao_negativo"),
            models.CheckConstraint(condition=Q(acrescimo__gte=0), name="ck_pdv_item_venda_acrescimo_nao_negativo"),
            models.CheckConstraint(condition=Q(total__gte=0), name="ck_pdv_item_venda_total_nao_negativo"),
        ]
        indexes = [
            models.Index(fields=["venda", "cancelado"]),
            models.Index(fields=["produto", "criado_em"]),
            models.Index(fields=["venda", "sequencia"]),
        ]

    def calcular_subtotal(self):
        return (Decimal(self.quantidade) * Decimal(self.preco_unitario)).quantize(Decimal("0.01"))

    def calcular_total(self):
        return (self.calcular_subtotal() - Decimal(self.desconto) + Decimal(self.acrescimo)).quantize(Decimal("0.01"))

    def recalcular(self):
        self.subtotal = self.calcular_subtotal()
        self.total = self.calcular_total()
        return self.total

    def clean(self):
        errors = {}
        if self.venda_id and self.produto_id and self.produto.matriz_id != self.venda.matriz_id:
            errors["produto"] = "O produto deve pertencer a mesma matriz da venda."
        if self.venda_id and self.venda.status in {"finalizada", "cancelada"}:
            errors["venda"] = "Nao e permitido alterar itens de uma venda encerrada."

        produto_ativo = True
        if self.produto_id:
            if hasattr(self.produto, "ativo"):
                produto_ativo = bool(self.produto.ativo)
            elif hasattr(self.produto, "status"):
                produto_ativo = self.produto.status not in {"inativo", "INATIVO"}
        if not produto_ativo:
            errors["produto"] = "O produto informado esta inativo."

        if self.quantidade <= Decimal("0.000"):
            errors["quantidade"] = "A quantidade deve ser maior que zero."
        if self.preco_unitario < Decimal("0.00"):
            errors["preco_unitario"] = "O preco unitario nao pode ser negativo."
        if self.desconto < Decimal("0.00"):
            errors["desconto"] = "O desconto nao pode ser negativo."
        if self.acrescimo < Decimal("0.00"):
            errors["acrescimo"] = "O acrescimo nao pode ser negativo."

        subtotal = self.calcular_subtotal()
        total = self.calcular_total()
        if self.desconto > subtotal + self.acrescimo:
            errors["desconto"] = "O desconto nao pode tornar o total do item negativo."
        if self.subtotal != subtotal:
            errors["subtotal"] = "O subtotal deve ser quantidade vezes preco unitario."
        if self.total != total:
            errors["total"] = "O total deve ser subtotal menos desconto mais acrescimo."
        if self.cancelado and not self.motivo_cancelamento.strip():
            errors["motivo_cancelamento"] = "Informe o motivo do cancelamento do item."
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.recalcular()
        self.full_clean()
        resultado = super().save(*args, **kwargs)
        if self.venda_id:
            self.venda.recalcular_totais()
        return resultado

    def delete(self, *args, **kwargs):
        raise ValidationError("Itens de venda nao podem ser excluidos. Utilize o cancelamento logico.")

    def __str__(self):
        return f"{self.venda} - item {self.sequencia}: {self.produto}"


class PagamentoVenda(models.Model):
    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        db_index=True,
    )
    venda = models.ForeignKey(
        Venda,
        on_delete=models.PROTECT,
        related_name="pagamentos",
    )
    forma_pagamento = models.ForeignKey(
        FormaPagamento,
        on_delete=models.PROTECT,
        related_name="pagamentos_venda",
    )
    valor = models.DecimalField(max_digits=14, decimal_places=2)
    parcelas = models.PositiveSmallIntegerField(default=1)
    valor_recebido = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        blank=True,
        null=True,
    )
    troco = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    referencia_externa = models.CharField(
        max_length=120,
        blank=True,
        db_index=True,
    )
    autorizado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="pagamentos_pdv_autorizados",
        blank=True,
        null=True,
    )
    observacao = models.TextField(blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["criado_em"]
        constraints = [
            models.CheckConstraint(
                condition=Q(valor__gt=0),
                name="ck_pdv_pagamento_valor_positivo",
            ),
            models.CheckConstraint(
                condition=Q(parcelas__gte=1),
                name="ck_pdv_pagamento_minimo_uma_parcela",
            ),
            models.CheckConstraint(
                condition=Q(troco__gte=0),
                name="ck_pdv_pagamento_troco_nao_negativo",
            ),
        ]
        indexes = [
            models.Index(fields=["venda", "forma_pagamento"]),
            models.Index(fields=["forma_pagamento", "criado_em"]),
        ]

    def clean(self):
        errors = {}
        forma = self.forma_pagamento
        venda = self.venda

        if forma.matriz_id != venda.matriz_id:
            errors["forma_pagamento"] = (
                "A forma de pagamento deve pertencer a matriz da venda."
            )

        if self.parcelas > forma.maximo_parcelas:
            errors["parcelas"] = "Quantidade de parcelas acima do limite permitido."

        if self.parcelas > 1 and not forma.permite_parcelamento:
            errors["parcelas"] = "Esta forma de pagamento nao permite parcelamento."

        if forma.exige_cliente_identificado:
            cliente = venda.cliente
            if not cliente or cliente.cpf == "CONSUMIDOR":
                errors["forma_pagamento"] = (
                    "Esta forma exige cliente identificado e nao aceita CONSUMIDOR."
                )

        if forma.exige_autorizacao and not self.autorizado_por_id:
            errors["autorizado_por"] = "Esta forma de pagamento exige autorizacao."

        if self.troco > 0 and not forma.permite_troco:
            errors["troco"] = "Esta forma de pagamento nao permite troco."

        if self.valor_recebido is not None:
            troco_calculado = self.valor_recebido - self.valor
            if troco_calculado < 0:
                errors["valor_recebido"] = "O valor recebido nao pode ser menor que o valor."
            elif self.troco != troco_calculado:
                errors["troco"] = "O troco informado nao corresponde ao valor recebido."

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.venda} - {self.forma_pagamento}: {self.valor}"


class MovimentacaoCaixa(models.Model):
    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        db_index=True,
    )
    sessao_caixa = models.ForeignKey(
        SessaoCaixa,
        on_delete=models.PROTECT,
        related_name="movimentacoes",
    )
    tipo = models.CharField(
        max_length=20,
        choices=TipoMovimentacaoCaixa.choices,
        db_index=True,
    )
    valor = models.DecimalField(max_digits=14, decimal_places=2)
    operador = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="movimentacoes_caixa_pdv",
    )
    venda = models.ForeignKey(
        Venda,
        on_delete=models.PROTECT,
        related_name="movimentacoes_caixa",
        blank=True,
        null=True,
    )
    movimentacao_estornada = models.OneToOneField(
        "self",
        on_delete=models.PROTECT,
        related_name="estorno_gerado",
        blank=True,
        null=True,
    )
    descricao = models.CharField(max_length=255, blank=True)
    criada_em = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["criada_em"]
        constraints = [
            models.CheckConstraint(
                condition=Q(valor__gt=0),
                name="ck_pdv_movimentacao_valor_positivo",
            ),
        ]
        indexes = [
            models.Index(fields=["sessao_caixa", "tipo"]),
            models.Index(fields=["sessao_caixa", "criada_em"]),
            models.Index(fields=["venda", "tipo"]),
        ]

    def clean(self):
        errors = {}

        if self.tipo == TipoMovimentacaoCaixa.VENDA and not self.venda_id:
            errors["venda"] = "Movimentacao de venda exige uma venda vinculada."

        if self.tipo == TipoMovimentacaoCaixa.ESTORNO and not self.movimentacao_estornada_id:
            errors["movimentacao_estornada"] = (
                "Movimentacao de estorno exige a movimentacao original."
            )

        if self.movimentacao_estornada_id:
            if self.movimentacao_estornada.sessao_caixa_id != self.sessao_caixa_id:
                errors["movimentacao_estornada"] = (
                    "O estorno deve pertencer a mesma sessao da movimentacao original."
                )

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        if self.pk:
            raise ValidationError(
                "Movimentacoes de caixa sao imutaveis. Registre um estorno."
            )
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError(
            "Movimentacoes de caixa nao podem ser excluidas. Registre um estorno."
        )

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.valor}"
