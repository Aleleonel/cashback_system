import uuid

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q

from fiscal.choices_documento_fiscal import (
    AmbienteDocumentoFiscal,
    ModeloDocumentoFiscal,
    StatusDocumentoFiscal,
)


STATUS_CONTEUDO_IMUTAVEL = {
    StatusDocumentoFiscal.AUTORIZADO,
    StatusDocumentoFiscal.DENEGADO,
    StatusDocumentoFiscal.CANCELADO,
}


class DocumentoFiscal(models.Model):
    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
    )

    venda_fiscal = models.ForeignKey(
        "pdv.VendaFiscal",
        on_delete=models.PROTECT,
        related_name="documentos_fiscais",
    )

    matriz = models.ForeignKey(
        "empresas.Matriz",
        on_delete=models.PROTECT,
        related_name="documentos_fiscais",
    )

    loja = models.ForeignKey(
        "empresas.Loja",
        on_delete=models.PROTECT,
        related_name="documentos_fiscais",
    )

    modelo = models.CharField(
        max_length=2,
        choices=ModeloDocumentoFiscal.choices,
    )

    ambiente = models.CharField(
        max_length=20,
        choices=AmbienteDocumentoFiscal.choices,
    )

    serie = models.PositiveSmallIntegerField()

    numero = models.PositiveBigIntegerField(
        null=True,
        blank=True,
    )

    chave_acesso = models.CharField(
        max_length=44,
        blank=True,
        default="",
    )

    codigo_numerico = models.CharField(
        max_length=8,
        blank=True,
        default="",
    )

    digito_verificador = models.CharField(
        max_length=1,
        blank=True,
        default="",
    )

    status = models.CharField(
        max_length=32,
        choices=StatusDocumentoFiscal.choices,
        default=StatusDocumentoFiscal.RASCUNHO,
        db_index=True,
    )

    tentativa_atual = models.PositiveIntegerField(
        default=0,
    )

    codigo_status = models.CharField(
        max_length=16,
        blank=True,
        default="",
    )

    motivo_status = models.TextField(
        blank=True,
        default="",
    )

    protocolo_autorizacao = models.CharField(
        max_length=64,
        blank=True,
        default="",
    )

    data_autorizacao = models.DateTimeField(
        null=True,
        blank=True,
    )

    xml_rascunho = models.TextField(
        blank=True,
        default="",
    )

    xml_assinado = models.TextField(
        blank=True,
        default="",
    )

    xml_autorizado = models.TextField(
        blank=True,
        default="",
    )

    idempotency_key = models.CharField(
        max_length=160,
        unique=True,
    )

    ultima_tentativa_em = models.DateTimeField(
        null=True,
        blank=True,
    )

    criado_em = models.DateTimeField(
        auto_now_add=True,
    )

    atualizado_em = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ("-criado_em", "-id")

        constraints = [
            models.UniqueConstraint(
                fields=(
                    "loja",
                    "modelo",
                    "ambiente",
                    "serie",
                    "numero",
                ),
                condition=Q(numero__isnull=False),
                name="uq_doc_fiscal_identidade_numerada",
            ),
            models.UniqueConstraint(
                fields=("chave_acesso",),
                condition=~Q(chave_acesso=""),
                name="uq_doc_fiscal_chave_preenchida",
            ),
            models.CheckConstraint(
                condition=Q(serie__gte=1),
                name="ck_doc_fiscal_serie_positiva",
            ),
            models.CheckConstraint(
                condition=Q(numero__isnull=True) | Q(numero__gte=1),
                name="ck_doc_fiscal_numero_positivo",
            ),
        ]

    def clean(self):
        errors = {}

        self.chave_acesso = (self.chave_acesso or "").strip()
        self.codigo_numerico = (self.codigo_numerico or "").strip()
        self.digito_verificador = (
            self.digito_verificador or ""
        ).strip()

        if self.serie is not None and self.serie < 1:
            errors["serie"] = "A serie deve ser maior que zero."

        if self.numero is not None and self.numero < 1:
            errors["numero"] = "O numero deve ser maior que zero."

        if self.chave_acesso:
            if (
                len(self.chave_acesso) != 44
                or not self.chave_acesso.isdigit()
            ):
                errors["chave_acesso"] = (
                    "A chave de acesso deve conter exatamente 44 digitos."
                )

        if self.codigo_numerico:
            if (
                len(self.codigo_numerico) != 8
                or not self.codigo_numerico.isdigit()
            ):
                errors["codigo_numerico"] = (
                    "O codigo numerico deve conter exatamente 8 digitos."
                )

        if self.digito_verificador:
            if (
                len(self.digito_verificador) != 1
                or not self.digito_verificador.isdigit()
            ):
                errors["digito_verificador"] = (
                    "O digito verificador deve conter um digito."
                )

        if errors:
            raise ValidationError(errors)

    def validar_conteudo_mutavel(self):
        if not self.pk:
            return

        anterior = (
            type(self)
            .objects
            .filter(pk=self.pk)
            .values(
                "status",
                "venda_fiscal_id",
                "matriz_id",
                "loja_id",
                "modelo",
                "ambiente",
                "serie",
                "numero",
                "chave_acesso",
                "codigo_numerico",
                "digito_verificador",
                "xml_autorizado",
                "protocolo_autorizacao",
            )
            .first()
        )

        if not anterior:
            return

        if anterior["status"] not in STATUS_CONTEUDO_IMUTAVEL:
            return

        protegidos = (
            "venda_fiscal_id",
            "matriz_id",
            "loja_id",
            "modelo",
            "ambiente",
            "serie",
            "numero",
            "chave_acesso",
            "codigo_numerico",
            "digito_verificador",
            "xml_autorizado",
            "protocolo_autorizacao",
        )

        alterados = [
            campo
            for campo in protegidos
            if anterior[campo] != getattr(self, campo)
        ]

        if alterados:
            raise ValidationError({
                "__all__": (
                    "Documento fiscal em estado terminal nao pode "
                    "ter seu conteudo fiscal alterado: "
                    + ", ".join(alterados)
                )
            })

    def save(self, *args, **kwargs):
        self.validar_conteudo_mutavel()
        return super().save(*args, **kwargs)

    def __str__(self):
        numero = self.numero if self.numero is not None else "sem-numero"

        return (
            f"{self.get_modelo_display()} "
            f"{self.serie}/{numero} "
            f"[{self.get_status_display()}]"
        )


class SequenciaDocumentoFiscal(models.Model):
    matriz = models.ForeignKey(
        "empresas.Matriz",
        on_delete=models.PROTECT,
        related_name="sequencias_documentos_fiscais",
    )

    loja = models.ForeignKey(
        "empresas.Loja",
        on_delete=models.PROTECT,
        related_name="sequencias_documentos_fiscais",
    )

    modelo = models.CharField(
        max_length=2,
        choices=ModeloDocumentoFiscal.choices,
    )

    ambiente = models.CharField(
        max_length=20,
        choices=AmbienteDocumentoFiscal.choices,
    )

    serie = models.PositiveSmallIntegerField()

    proximo_numero = models.PositiveBigIntegerField(
        default=1,
    )

    atualizado_em = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=(
                    "loja",
                    "modelo",
                    "ambiente",
                    "serie",
                ),
                name="uq_sequencia_doc_fiscal_escopo",
            ),
            models.CheckConstraint(
                condition=Q(serie__gte=1),
                name="ck_seq_doc_fiscal_serie_positiva",
            ),
            models.CheckConstraint(
                condition=Q(proximo_numero__gte=1),
                name="ck_seq_doc_fiscal_numero_positivo",
            ),
        ]

    def __str__(self):
        return (
            f"{self.loja_id} "
            f"{self.modelo} "
            f"{self.ambiente} "
            f"serie {self.serie} -> {self.proximo_numero}"
        )