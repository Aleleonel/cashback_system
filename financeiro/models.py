import uuid

from django.db import models
from django.db.models import Q



class PlanoConta(models.Model):
    class Tipo(models.TextChoices):
        SINTETICA = "SINTETICA", "Sintética"
        ANALITICA = "ANALITICA", "Analítica"

    class Natureza(models.TextChoices):
        DESPESA = "DESPESA", "Despesa"
        RECEITA = "RECEITA", "Receita"
        ATIVO = "ATIVO", "Ativo"
        PASSIVO = "PASSIVO", "Passivo"
        OUTRO = "OUTRO", "Outro"

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    matriz = models.ForeignKey(
        "empresas.Matriz",
        on_delete=models.PROTECT,
        related_name="planos_contas_financeiros",
    )
    codigo = models.CharField(max_length=30)
    nome = models.CharField(max_length=150)
    tipo = models.CharField(max_length=10, choices=Tipo.choices)
    natureza = models.CharField(max_length=10, choices=Natureza.choices)
    pai = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        related_name="filhos",
        null=True,
        blank=True,
    )
    nivel = models.PositiveSmallIntegerField(default=1)
    aceita_lancamento = models.BooleanField(default=True)
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["matriz", "codigo"],
                name="uq_fin_plano_matriz_codigo",
            ),
        ]
        indexes = [
            models.Index(fields=["matriz", "ativo"], name="ix_fin_plano_mat_ativo"),
            models.Index(fields=["matriz", "natureza"], name="ix_fin_plano_mat_nat"),
        ]
    def __str__(self):
        return f"{self.codigo} - {self.nome}"



class CentroCusto(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    matriz = models.ForeignKey(
        "empresas.Matriz",
        on_delete=models.PROTECT,
        related_name="centros_custo_financeiros",
    )
    codigo = models.CharField(max_length=30)
    nome = models.CharField(max_length=150)

    def __str__(self):
        return f"{self.codigo} - {self.nome}"
    descricao = models.TextField(blank=True)
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["matriz", "codigo"],
                name="uq_fin_cc_matriz_codigo",
            ),
        ]
        indexes = [
            models.Index(fields=["matriz", "ativo"], name="ix_fin_cc_mat_ativo"),
        ]


class InstituicaoBancaria(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    codigo_bacen = models.CharField(max_length=10, null=True, blank=True)
    nome = models.CharField(max_length=150)
    ativo = models.BooleanField(default=True)

    def __str__(self):
        if self.codigo_bacen:
            return f"{self.codigo_bacen} - {self.nome}"
        return self.nome
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["codigo_bacen"],
                condition=Q(codigo_bacen__isnull=False) & ~Q(codigo_bacen=""),
                name="uq_fin_banco_codigo_bacen",
            ),
        ]
        indexes = [
            models.Index(fields=["nome"], name="ix_fin_banco_nome"),
        ]


class ContaFinanceira(models.Model):
    class Tipo(models.TextChoices):
        CONTA_CORRENTE = "CONTA_CORRENTE", "Conta corrente"
        POUPANCA = "POUPANCA", "Poupança"
        CARTEIRA_DIGITAL = "CARTEIRA_DIGITAL", "Carteira digital"
        OUTRA = "OUTRA", "Outra"

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    matriz = models.ForeignKey(
        "empresas.Matriz",
        on_delete=models.PROTECT,
        related_name="contas_financeiras",
    )
    loja = models.ForeignKey(
        "empresas.Loja",
        on_delete=models.PROTECT,
        related_name="contas_financeiras",
        null=True,
        blank=True,
    )
    instituicao = models.ForeignKey(
        InstituicaoBancaria,
        on_delete=models.PROTECT,
        related_name="contas_financeiras",
        null=True,
        blank=True,
    )
    tipo = models.CharField(max_length=20, choices=Tipo.choices)
    nome = models.CharField(max_length=150)
    agencia = models.CharField(max_length=20, blank=True)
    numero = models.CharField(max_length=30, blank=True)
    digito = models.CharField(max_length=10, blank=True)
    chave_pix = models.CharField(max_length=150, blank=True)
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["matriz", "ativo"], name="ix_fin_conta_mat_ativo"),
            models.Index(fields=["matriz", "loja", "ativo"], name="ix_fin_conta_mat_loja"),
        ]
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
    plano_conta = models.ForeignKey(
        "PlanoConta",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="titulos_financeiros",
    )
    centro_custo = models.ForeignKey(
        "CentroCusto",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="titulos_financeiros",
    )
    entidade_nome = models.CharField(max_length=255, blank=True)
    documento_referencia = models.CharField(max_length=100, blank=True)
    descricao = models.CharField(max_length=255)
    valor_original = models.DecimalField(max_digits=14, decimal_places=2)
    data_competencia = models.DateField(null=True, blank=True)
    valor_bruto = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    valor_desconto = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    valor_juros = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    observacao = models.TextField(blank=True)
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
    forma_pagamento = models.ForeignKey(
        "pdv.FormaPagamento",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="baixas_financeiras",
    )
    conta_financeira = models.ForeignKey(
        "ContaFinanceira",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="baixas_financeiras",
    )
    sessao_caixa = models.ForeignKey(
        "pdv.SessaoCaixa",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="baixas_financeiras",
    )
    movimentacao_caixa = models.ForeignKey(
        "pdv.MovimentacaoCaixa",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="baixas_financeiras",
    )
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
