from django.core.exceptions import ValidationError
from django.db import models

from fiscal.choices_documento_fiscal import AmbienteDocumentoFiscal


class ConfiguracaoEmissaoFiscalLoja(models.Model):
    """Identidade fiscal e parametros NAO SECRETOS de emissao por estabelecimento."""

    loja = models.OneToOneField(
        "empresas.Loja",
        on_delete=models.PROTECT,
        related_name="configuracao_emissao_fiscal",
    )
    razao_social = models.CharField(max_length=150)
    nome_fantasia = models.CharField(max_length=150, blank=True, default="")
    inscricao_estadual = models.CharField(max_length=20)
    logradouro = models.CharField(max_length=150)
    numero = models.CharField(max_length=20)
    complemento = models.CharField(max_length=100, blank=True, default="")
    bairro = models.CharField(max_length=100)
    municipio = models.CharField(max_length=100)
    codigo_municipio_ibge = models.CharField(max_length=7)
    uf = models.CharField(max_length=2)
    cep = models.CharField(max_length=8)
    crt = models.CharField(max_length=2)
    ambiente_nfce = models.CharField(
        max_length=20,
        choices=AmbienteDocumentoFiscal.choices,
        default=AmbienteDocumentoFiscal.HOMOLOGACAO,
    )
    serie_nfce = models.PositiveSmallIntegerField(default=1)
    certificado_a1_referencia = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text=(
            "Referencia nao secreta para localizar o certificado A1 fora do repositorio. "
            "Nao armazene senha, chave privada ou conteudo do certificado neste campo."
        ),
    )
    certificado_a1_segredo_referencia = models.CharField(
        max_length=500,
        blank=True,
        default="",
        help_text=(
            "Referencia opaca do secret da senha A1. "
            "Nunca armazene a senha neste campo."
        ),
    )
    ativa = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("loja_id",)
        verbose_name = "configuracao de emissao fiscal da loja"
        verbose_name_plural = "configurações de emissao fiscal das lojas"

    def __str__(self):
        return f"{self.loja} - NFC-e serie {self.serie_nfce}"

    def clean(self):
        errors = {}
        self.razao_social = (self.razao_social or "").strip()
        self.nome_fantasia = (self.nome_fantasia or "").strip()
        self.inscricao_estadual = (self.inscricao_estadual or "").strip()
        self.logradouro = (self.logradouro or "").strip()
        self.numero = (self.numero or "").strip()
        self.complemento = (self.complemento or "").strip()
        self.bairro = (self.bairro or "").strip()
        self.municipio = (self.municipio or "").strip()
        self.codigo_municipio_ibge = (self.codigo_municipio_ibge or "").strip()
        self.uf = (self.uf or "").strip().upper()
        self.cep = "".join(ch for ch in (self.cep or "") if ch.isdigit())
        self.crt = (self.crt or "").strip()

        if len(self.uf) != 2:
            errors["uf"] = "A UF deve possuir 2 caracteres."
        if len(self.codigo_municipio_ibge) != 7 or not self.codigo_municipio_ibge.isdigit():
            errors["codigo_municipio_ibge"] = "O codigo IBGE do municipio deve possuir 7 digitos."
        if len(self.cep) != 8:
            errors["cep"] = "O CEP deve possuir 8 digitos."
        if self.serie_nfce < 1:
            errors["serie_nfce"] = "A serie NFC-e deve ser maior que zero."
        if errors:
            raise ValidationError(errors)
