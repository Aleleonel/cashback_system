from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models


class BeneficioFiscal(models.Model):
    TIPO_ISENCAO = "isencao"
    TIPO_REDUCAO_BASE = "reducao_base"
    TIPO_DIFERIMENTO = "diferimento"
    TIPO_CREDITO_PRESUMIDO = "credito_presumido"
    TIPO_DESONERACAO = "desoneracao"
    TIPO_IMUNIDADE = "imunidade"
    TIPO_SUSPENSAO = "suspensao"
    TIPO_OUTROS = "outros"

    TIPO_BENEFICIO_CHOICES = (
        (TIPO_ISENCAO, "Isencao"),
        (TIPO_REDUCAO_BASE, "Reducao de base"),
        (TIPO_DIFERIMENTO, "Diferimento"),
        (TIPO_CREDITO_PRESUMIDO, "Credito presumido"),
        (TIPO_DESONERACAO, "Desoneracao"),
        (TIPO_IMUNIDADE, "Imunidade"),
        (TIPO_SUSPENSAO, "Suspensao"),
        (TIPO_OUTROS, "Outros"),
    )

    REGIME_TODOS = "todos"
    REGIME_NORMAL = "normal"
    REGIME_SIMPLES = "simples"
    REGIME_MEI = "mei"

    REGIME_TRIBUTARIO_CHOICES = (
        (REGIME_TODOS, "Todos"),
        (REGIME_NORMAL, "Regime normal"),
        (REGIME_SIMPLES, "Simples Nacional"),
        (REGIME_MEI, "MEI"),
    )

    codigo = models.CharField(
        "Codigo",
        max_length=20,
        unique=True,
        db_index=True,
    )
    descricao = models.TextField(
        "Descricao",
    )
    uf = models.CharField(
        "UF",
        max_length=2,
        blank=True,
        db_index=True,
    )
    tipo_beneficio = models.CharField(
        "Tipo de beneficio",
        max_length=24,
        choices=TIPO_BENEFICIO_CHOICES,
        db_index=True,
    )
    fundamento_legal = models.TextField(
        "Fundamento legal",
        blank=True,
    )
    percentual_reducao = models.DecimalField(
        "Percentual de reducao",
        max_digits=7,
        decimal_places=4,
        null=True,
        blank=True,
    )
    percentual_credito = models.DecimalField(
        "Percentual de credito",
        max_digits=7,
        decimal_places=4,
        null=True,
        blank=True,
    )
    exige_motivo_desoneracao = models.BooleanField(
        "Exige motivo de desoneracao",
        default=False,
    )
    motivo_desoneracao_padrao = models.CharField(
        "Motivo de desoneracao padrao",
        max_length=2,
        blank=True,
    )
    regime_tributario = models.CharField(
        "Regime tributario",
        max_length=12,
        choices=REGIME_TRIBUTARIO_CHOICES,
        default=REGIME_TODOS,
        db_index=True,
    )
    vigencia_inicio = models.DateField(
        "Inicio da vigencia",
        null=True,
        blank=True,
    )
    vigencia_fim = models.DateField(
        "Fim da vigencia",
        null=True,
        blank=True,
    )
    ativo = models.BooleanField(
        "Ativo",
        default=True,
        db_index=True,
    )
    criado_em = models.DateTimeField(
        "Criado em",
        auto_now_add=True,
    )
    atualizado_em = models.DateTimeField(
        "Atualizado em",
        auto_now=True,
    )

    class Meta:
        db_table = "fiscal_beneficio_fiscal"
        verbose_name = "Beneficio fiscal"
        verbose_name_plural = "Beneficios fiscais"
        ordering = ("codigo",)
        indexes = [
            models.Index(
                fields=("ativo", "codigo"),
                name="fiscal_ben_ativo_cod_idx",
            ),
            models.Index(
                fields=("uf", "tipo_beneficio"),
                name="fiscal_ben_uf_tipo_idx",
            ),
            models.Index(
                fields=("regime_tributario", "ativo"),
                name="fiscal_ben_reg_ativo_idx",
            ),
        ]

    @staticmethod
    def normalizar_codigo(codigo):
        return (codigo or "").strip().upper()

    @staticmethod
    def normalizar_uf(uf):
        return (uf or "").strip().upper()

    def clean(self):
        erros = {}

        self.codigo = self.normalizar_codigo(self.codigo)
        self.descricao = (self.descricao or "").strip()
        self.uf = self.normalizar_uf(self.uf)
        self.fundamento_legal = (
            self.fundamento_legal or ""
        ).strip()
        self.motivo_desoneracao_padrao = (
            self.motivo_desoneracao_padrao or ""
        ).strip()

        if not self.codigo:
            erros["codigo"] = (
                "Informe o codigo do beneficio fiscal."
            )

        if len(self.codigo) > 20:
            erros["codigo"] = (
                "O codigo deve possuir no maximo vinte caracteres."
            )

        if not self.descricao:
            erros["descricao"] = (
                "Informe a descricao do beneficio fiscal."
            )

        ufs_validas = {
            "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES",
            "GO", "MA", "MT", "MS", "MG", "PA", "PB", "PR",
            "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC",
            "SP", "SE", "TO",
        }

        if self.uf and self.uf not in ufs_validas:
            erros["uf"] = "Informe uma UF valida."

        tipos_validos = {
            valor
            for valor, _ in self.TIPO_BENEFICIO_CHOICES
        }
        if self.tipo_beneficio not in tipos_validos:
            erros["tipo_beneficio"] = (
                "Informe um tipo de beneficio valido."
            )

        regimes_validos = {
            valor
            for valor, _ in self.REGIME_TRIBUTARIO_CHOICES
        }
        if self.regime_tributario not in regimes_validos:
            erros["regime_tributario"] = (
                "Informe um regime tributario valido."
            )

        for campo in (
            "percentual_reducao",
            "percentual_credito",
        ):
            valor = getattr(self, campo)
            if valor is not None and (
                valor < Decimal("0")
                or valor > Decimal("100")
            ):
                erros[campo] = (
                    "O percentual deve estar entre zero e cem."
                )

        if (
            self.vigencia_inicio
            and self.vigencia_fim
            and self.vigencia_fim < self.vigencia_inicio
        ):
            erros["vigencia_fim"] = (
                "O fim da vigencia nao pode ser anterior ao inicio."
            )

        if (
            self.exige_motivo_desoneracao
            and not self.motivo_desoneracao_padrao
        ):
            erros["motivo_desoneracao_padrao"] = (
                "Informe o motivo de desoneracao padrao."
            )

        if erros:
            raise ValidationError(erros)

    def save(self, *args, **kwargs):
        self.codigo = self.normalizar_codigo(self.codigo)
        self.descricao = (self.descricao or "").strip()
        self.uf = self.normalizar_uf(self.uf)
        self.fundamento_legal = (
            self.fundamento_legal or ""
        ).strip()
        self.motivo_desoneracao_padrao = (
            self.motivo_desoneracao_padrao or ""
        ).strip()
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        sufixo = f" - {self.uf}" if self.uf else ""
        return f"{self.codigo}{sufixo} - {self.descricao}"
