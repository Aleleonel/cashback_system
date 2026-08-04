from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models


class NCM(models.Model):
    codigo = models.CharField(
        "Codigo",
        max_length=8,
        unique=True,
        db_index=True,
        validators=[
            RegexValidator(
                regex=r"^\d{8}$",
                message="O codigo deve conter exatamente oito digitos.",
            )
        ],
    )
    descricao = models.TextField("Descricao")
    unidade_tributavel_padrao = models.CharField(
        "Unidade tributavel padrao",
        max_length=10,
        blank=True,
    )
    ativo = models.BooleanField("Ativo", default=True, db_index=True)
    criado_em = models.DateTimeField("Criado em", auto_now_add=True)
    atualizado_em = models.DateTimeField("Atualizado em", auto_now=True)

    class Meta:
        db_table = "fiscal_ncm"
        verbose_name = "NCM"
        verbose_name_plural = "NCM"
        ordering = ("codigo",)
        indexes = [
            models.Index(
                fields=("ativo", "codigo"),
                name="fiscal_ncm_ativo_cod_idx",
            ),
        ]

    @staticmethod
    def normalizar_codigo(codigo):
        return "".join(
            caractere
            for caractere in str(codigo or "")
            if caractere.isdigit()
        )

    def clean(self):
        erros = {}
        self.codigo = self.normalizar_codigo(self.codigo)
        self.descricao = (self.descricao or "").strip()
        self.unidade_tributavel_padrao = (
            self.unidade_tributavel_padrao or ""
        ).strip().upper()

        if len(self.codigo) != 8:
            erros["codigo"] = (
                "O codigo deve conter exatamente oito digitos."
            )

        if not self.descricao:
            erros["descricao"] = "Informe a descricao do NCM."

        if erros:
            raise ValidationError(erros)

    def save(self, *args, **kwargs):
        self.codigo = self.normalizar_codigo(self.codigo)
        self.descricao = (self.descricao or "").strip()
        self.unidade_tributavel_padrao = (
            self.unidade_tributavel_padrao or ""
        ).strip().upper()
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.codigo} - {self.descricao}"
