from django.core.exceptions import ValidationError
from django.db import models

from empresas.models import Matriz
from fiscal.models_regra_fiscal import RegraFiscal, UFS_VALIDAS


class ConfiguracaoFiscalMatriz(models.Model):
    matriz = models.OneToOneField(
        Matriz,
        on_delete=models.PROTECT,
        related_name="configuracao_fiscal",
        verbose_name="Matriz",
    )
    regime_tributario = models.CharField(
        "Regime tributario",
        max_length=12,
        choices=RegraFiscal.REGIME_TRIBUTARIO_CHOICES,
    )
    uf_origem = models.CharField("UF de origem", max_length=2)
    contribuinte_icms = models.BooleanField("Contribuinte do ICMS")
    consumidor_final_padrao = models.BooleanField(
        "Consumidor final padrao"
    )
    ativa = models.BooleanField("Ativa", default=True, db_index=True)
    observacoes = models.TextField("Observacoes", blank=True)
    criado_em = models.DateTimeField("Criado em", auto_now_add=True)
    atualizado_em = models.DateTimeField("Atualizado em", auto_now=True)

    class Meta:
        db_table = "fiscal_configuracao_fiscal_matriz"
        verbose_name = "Configuracao fiscal da matriz"
        verbose_name_plural = "Configuracoes fiscais das matrizes"
        ordering = ("matriz__nome",)

    def clean(self):
        erros = {}
        self.uf_origem = RegraFiscal.normalizar_uf(self.uf_origem)
        self.observacoes = (self.observacoes or "").strip()

        regimes = {
            valor
            for valor, _ in RegraFiscal.REGIME_TRIBUTARIO_CHOICES
        }
        if self.regime_tributario not in regimes:
            erros["regime_tributario"] = (
                "Informe um regime tributario valido."
            )
        if not self.uf_origem:
            erros["uf_origem"] = "Informe a UF de origem."
        elif self.uf_origem not in UFS_VALIDAS:
            erros["uf_origem"] = "Informe uma UF brasileira valida."

        if erros:
            raise ValidationError(erros)

    def save(self, *args, **kwargs):
        self.uf_origem = RegraFiscal.normalizar_uf(self.uf_origem)
        self.observacoes = (self.observacoes or "").strip()
        self.full_clean()
        return super().save(*args, **kwargs)

    @property
    def pronta_para_operacao(self):
        return bool(
            self.ativa
            and self.regime_tributario
            and self.uf_origem
        )

    def __str__(self):
        return f"Configuracao fiscal - {self.matriz.nome}"
