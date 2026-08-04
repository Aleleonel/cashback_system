from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models


class CFOP(models.Model):
    TIPO_ENTRADA = "entrada"
    TIPO_SAIDA = "saida"
    TIPO_OPERACAO_CHOICES = (
        (TIPO_ENTRADA, "Entrada"),
        (TIPO_SAIDA, "Saida"),
    )

    DESTINO_INTERNA = "interna"
    DESTINO_INTERESTADUAL = "interestadual"
    DESTINO_EXTERIOR = "exterior"
    DESTINO_OPERACAO_CHOICES = (
        (DESTINO_INTERNA, "Interna"),
        (DESTINO_INTERESTADUAL, "Interestadual"),
        (DESTINO_EXTERIOR, "Exterior"),
    )

    codigo = models.CharField(
        "Codigo",
        max_length=4,
        unique=True,
        db_index=True,
        validators=[
            RegexValidator(
                regex=r"^[123567]\d{3}$",
                message="O codigo deve conter quatro digitos e iniciar por 1, 2, 3, 5, 6 ou 7.",
            )
        ],
    )
    descricao = models.CharField("Descricao", max_length=260)
    tipo_operacao = models.CharField(
        "Tipo de operacao",
        max_length=10,
        choices=TIPO_OPERACAO_CHOICES,
        db_index=True,
        editable=False,
    )
    destino_operacao = models.CharField(
        "Destino da operacao",
        max_length=15,
        choices=DESTINO_OPERACAO_CHOICES,
        db_index=True,
        editable=False,
    )
    gera_movimento_estoque = models.BooleanField("Gera movimento de estoque", default=True)
    permite_devolucao = models.BooleanField("Permite devolucao", default=False)
    permite_remessa = models.BooleanField("Permite remessa", default=False)
    ativo = models.BooleanField("Ativo", default=True, db_index=True)
    criado_em = models.DateTimeField("Criado em", auto_now_add=True)
    atualizado_em = models.DateTimeField("Atualizado em", auto_now=True)

    class Meta:
        db_table = "fiscal_cfop"
        verbose_name = "CFOP"
        verbose_name_plural = "CFOP"
        ordering = ("codigo",)
        indexes = [
            models.Index(fields=("ativo", "codigo"), name="fiscal_cfop_ativo_cod_idx"),
            models.Index(fields=("tipo_operacao", "destino_operacao"), name="fiscal_cfop_tipo_dest_idx"),
        ]

    @classmethod
    def classificar_codigo(cls, codigo):
        codigo = (codigo or "").strip()
        if len(codigo) != 4 or not codigo.isdigit() or codigo[0] not in "123567":
            raise ValidationError({
                "codigo": "O codigo deve conter quatro digitos e iniciar por 1, 2, 3, 5, 6 ou 7."
            })

        primeiro = codigo[0]
        tipo = cls.TIPO_ENTRADA if primeiro in "123" else cls.TIPO_SAIDA

        if primeiro in "15":
            destino = cls.DESTINO_INTERNA
        elif primeiro in "26":
            destino = cls.DESTINO_INTERESTADUAL
        else:
            destino = cls.DESTINO_EXTERIOR

        return tipo, destino

    def clean(self):
        erros = {}
        self.codigo = (self.codigo or "").strip()
        self.descricao = (self.descricao or "").strip()

        try:
            self.tipo_operacao, self.destino_operacao = self.classificar_codigo(self.codigo)
        except ValidationError as erro:
            erros.update(erro.message_dict)

        if not self.descricao:
            erros["descricao"] = "Informe a descricao do CFOP."

        if erros:
            raise ValidationError(erros)

    def save(self, *args, **kwargs):
        self.codigo = (self.codigo or "").strip()
        self.descricao = (self.descricao or "").strip()
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.codigo} - {self.descricao}"
