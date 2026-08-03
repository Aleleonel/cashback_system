from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models


class CEST(models.Model):
    codigo = models.CharField(
        "Codigo",
        max_length=7,
        unique=True,
        db_index=True,
        validators=[
            RegexValidator(
                regex=r"^\d{7}$",
                message="O codigo deve conter exatamente sete digitos.",
            )
        ],
    )
    descricao = models.TextField("Descricao")
    segmento = models.CharField(
        "Segmento",
        max_length=160,
        blank=True,
        db_index=True,
    )
    ncm_referencia = models.CharField(
        "NCM de referencia",
        max_length=8,
        blank=True,
        db_index=True,
    )
    excecao = models.CharField(
        "Excecao",
        max_length=120,
        blank=True,
    )
    versao_tabela = models.CharField(
        "Versao da tabela",
        max_length=40,
        blank=True,
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
        db_table = "fiscal_cest"
        verbose_name = "CEST"
        verbose_name_plural = "CEST"
        ordering = ("codigo",)
        indexes = [
            models.Index(
                fields=("ativo", "codigo"),
                name="fiscal_cest_ativo_cod_idx",
            ),
            models.Index(
                fields=("segmento", "ativo"),
                name="fiscal_cest_seg_ativo_idx",
            ),
            models.Index(
                fields=("ncm_referencia", "ativo"),
                name="fiscal_cest_ncm_ativo_idx",
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
        self.ncm_referencia = self.normalizar_codigo(
            self.ncm_referencia
        )
        self.descricao = (self.descricao or "").strip()
        self.segmento = (self.segmento or "").strip()
        self.excecao = (self.excecao or "").strip()
        self.versao_tabela = (
            self.versao_tabela or ""
        ).strip()

        if len(self.codigo) != 7:
            erros["codigo"] = (
                "O codigo deve conter exatamente sete digitos."
            )

        if not self.descricao:
            erros["descricao"] = (
                "Informe a descricao do CEST."
            )

        if (
            self.ncm_referencia
            and len(self.ncm_referencia) != 8
        ):
            erros["ncm_referencia"] = (
                "O NCM de referencia deve conter oito digitos."
            )

        if (
            self.vigencia_inicio
            and self.vigencia_fim
            and self.vigencia_fim < self.vigencia_inicio
        ):
            erros["vigencia_fim"] = (
                "O fim da vigencia nao pode ser anterior ao inicio."
            )

        if erros:
            raise ValidationError(erros)

    def save(self, *args, **kwargs):
        self.codigo = self.normalizar_codigo(self.codigo)
        self.ncm_referencia = self.normalizar_codigo(
            self.ncm_referencia
        )
        self.descricao = (self.descricao or "").strip()
        self.segmento = (self.segmento or "").strip()
        self.excecao = (self.excecao or "").strip()
        self.versao_tabela = (
            self.versao_tabela or ""
        ).strip()
        self.full_clean()
        return super().save(*args, **kwargs)

    @property
    def codigo_formatado(self):
        if len(self.codigo) != 7:
            return self.codigo
        return (
            f"{self.codigo[:2]}."
            f"{self.codigo[2:5]}."
            f"{self.codigo[5:]}"
        )

    def __str__(self):
        return f"{self.codigo_formatado} - {self.descricao}"
