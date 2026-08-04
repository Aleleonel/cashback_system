from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models

class CSTICMS(models.Model):
    codigo = models.CharField("Codigo", max_length=2, unique=True, db_index=True, validators=[RegexValidator(regex=r"^\d{2}$", message="O codigo deve conter exatamente dois digitos.")])
    descricao = models.CharField("Descricao", max_length=220)
    exige_aliquota = models.BooleanField("Exige aliquota", default=False)
    permite_reducao_base = models.BooleanField("Permite reducao de base", default=False)
    permite_diferimento = models.BooleanField("Permite diferimento", default=False)
    permite_substituicao_tributaria = models.BooleanField("Permite substituicao tributaria", default=False)
    ativo = models.BooleanField("Ativo", default=True, db_index=True)
    criado_em = models.DateTimeField("Criado em", auto_now_add=True)
    atualizado_em = models.DateTimeField("Atualizado em", auto_now=True)

    class Meta:
        db_table = "fiscal_cst_icms"
        verbose_name = "CST ICMS"
        verbose_name_plural = "CST ICMS"
        ordering = ("codigo",)
        indexes = [models.Index(fields=("ativo", "codigo"), name="fiscal_csticms_ativo_cod_idx")]

    def clean(self):
        erros = {}
        self.codigo = (self.codigo or "").strip()
        self.descricao = (self.descricao or "").strip()
        if len(self.codigo) != 2 or not self.codigo.isdigit():
            erros["codigo"] = "O codigo deve conter exatamente dois digitos."
        if not self.descricao:
            erros["descricao"] = "Informe a descricao do CST ICMS."
        if erros:
            raise ValidationError(erros)

    def save(self, *args, **kwargs):
        self.codigo = (self.codigo or "").strip()
        self.descricao = (self.descricao or "").strip()
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.codigo} - {self.descricao}"
