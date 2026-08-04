from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models


class OrigemMercadoria(models.Model):
    codigo = models.CharField(
        "Codigo",
        max_length=1,
        unique=True,
        db_index=True,
        validators=[
            RegexValidator(
                regex=r"^[0-8]$",
                message="O codigo deve ser um digito entre 0 e 8.",
            )
        ],
    )
    descricao = models.CharField(
        "Descricao",
        max_length=180,
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
        db_table = "fiscal_origem_mercadoria"
        verbose_name = "Origem da mercadoria"
        verbose_name_plural = "Origens da mercadoria"
        ordering = ("codigo",)
        indexes = [
            models.Index(
                fields=("ativo", "codigo"),
                name="fiscal_orig_ativo_cod_idx",
            ),
        ]

    def clean(self):
        erros = {}

        self.codigo = (self.codigo or "").strip()
        self.descricao = (self.descricao or "").strip()

        if not self.codigo:
            erros["codigo"] = "Informe o codigo da origem."

        if self.codigo and (
            len(self.codigo) != 1
            or not self.codigo.isdigit()
            or self.codigo not in "012345678"
        ):
            erros["codigo"] = "O codigo deve ser um digito entre 0 e 8."

        if not self.descricao:
            erros["descricao"] = "Informe a descricao da origem."

        if erros:
            raise ValidationError(erros)

    def save(self, *args, **kwargs):
        self.codigo = (self.codigo or "").strip()
        self.descricao = (self.descricao or "").strip()
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.codigo} - {self.descricao}"

from fiscal.models_cst_icms import CSTICMS

from fiscal.models_csosn import CSOSN

from fiscal.models_cfop import CFOP

from fiscal.models_ncm import NCM

from fiscal.models_cst_pis import CSTPIS

from fiscal.models_cst_cofins import CSTCOFINS

from fiscal.models_cst_ipi import CSTIPI

from fiscal.models_cest import CEST

from fiscal.models_beneficio_fiscal import BeneficioFiscal

from fiscal.models_regra_fiscal import RegraFiscal
