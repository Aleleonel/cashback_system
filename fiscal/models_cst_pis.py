from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models


class CSTPIS(models.Model):
    TIPO_ENTRADA = "entrada"
    TIPO_SAIDA = "saida"
    TIPO_AMBOS = "ambos"

    TIPO_OPERACAO_CHOICES = (
        (TIPO_ENTRADA, "Entrada"),
        (TIPO_SAIDA, "Saida"),
        (TIPO_AMBOS, "Entrada e saida"),
    )

    codigo = models.CharField(
        "Codigo",
        max_length=2,
        unique=True,
        db_index=True,
        validators=[
            RegexValidator(
                regex=r"^\d{2}$",
                message="O codigo deve conter exatamente dois digitos.",
            )
        ],
    )
    descricao = models.CharField("Descricao", max_length=240)
    tipo_operacao = models.CharField(
        "Tipo de operacao",
        max_length=10,
        choices=TIPO_OPERACAO_CHOICES,
        db_index=True,
    )
    tributado = models.BooleanField("Operacao tributada", default=False)
    exige_aliquota = models.BooleanField("Exige aliquota", default=False)
    permite_credito = models.BooleanField("Permite credito", default=False)
    exige_base_calculo = models.BooleanField("Exige base de calculo", default=False)
    ativo = models.BooleanField("Ativo", default=True, db_index=True)
    criado_em = models.DateTimeField("Criado em", auto_now_add=True)
    atualizado_em = models.DateTimeField("Atualizado em", auto_now=True)

    class Meta:
        db_table = "fiscal_cst_pis"
        verbose_name = "CST PIS"
        verbose_name_plural = "CST PIS"
        ordering = ("codigo",)
        indexes = [
            models.Index(
                fields=("ativo", "codigo"),
                name="fiscal_cstpis_ativo_cod_idx",
            ),
            models.Index(
                fields=("tipo_operacao", "ativo"),
                name="fiscal_cstpis_tipo_ativo_idx",
            ),
        ]

    def clean(self):
        erros = {}
        self.codigo = (self.codigo or "").strip()
        self.descricao = (self.descricao or "").strip()

        if len(self.codigo) != 2 or not self.codigo.isdigit():
            erros["codigo"] = "O codigo deve conter exatamente dois digitos."

        if not self.descricao:
            erros["descricao"] = "Informe a descricao do CST PIS."

        if self.tipo_operacao not in {
            self.TIPO_ENTRADA,
            self.TIPO_SAIDA,
            self.TIPO_AMBOS,
        }:
            erros["tipo_operacao"] = "Informe um tipo de operacao valido."

        if erros:
            raise ValidationError(erros)

    def save(self, *args, **kwargs):
        self.codigo = (self.codigo or "").strip()
        self.descricao = (self.descricao or "").strip()
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.codigo} - {self.descricao}"
