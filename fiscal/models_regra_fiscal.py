from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q

from empresas.models import Loja, Matriz


UFS_VALIDAS = {
    "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES",
    "GO", "MA", "MT", "MS", "MG", "PA", "PB", "PR",
    "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC",
    "SP", "SE", "TO",
}


class RegraFiscal(models.Model):
    TIPO_ENTRADA = "entrada"
    TIPO_SAIDA = "saida"
    TIPO_AMBOS = "ambos"

    TIPO_OPERACAO_CHOICES = (
        (TIPO_ENTRADA, "Entrada"),
        (TIPO_SAIDA, "Saida"),
        (TIPO_AMBOS, "Entrada e saida"),
    )

    FINALIDADE_VENDA = "venda"
    FINALIDADE_COMPRA = "compra"
    FINALIDADE_DEVOLUCAO = "devolucao"
    FINALIDADE_REMESSA = "remessa"
    FINALIDADE_TRANSFERENCIA = "transferencia"

    FINALIDADE_OPERACAO_CHOICES = (
        (FINALIDADE_VENDA, "Venda"),
        (FINALIDADE_COMPRA, "Compra"),
        (FINALIDADE_DEVOLUCAO, "Devolucao"),
        (FINALIDADE_REMESSA, "Remessa"),
        (FINALIDADE_TRANSFERENCIA, "Transferencia"),
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

    nome = models.CharField(
        "Nome",
        max_length=180,
    )
    codigo_interno = models.CharField(
        "Codigo interno",
        max_length=40,
        unique=True,
        db_index=True,
    )
    descricao = models.TextField(
        "Descricao",
        blank=True,
    )
    prioridade = models.PositiveIntegerField(
        "Prioridade",
        default=100,
        db_index=True,
        help_text="Menor numero possui maior prioridade.",
    )
    ativo = models.BooleanField(
        "Ativo",
        default=True,
        db_index=True,
    )

    matriz = models.ForeignKey(
        Matriz,
        on_delete=models.PROTECT,
        related_name="regras_fiscais",
        null=True,
        blank=True,
        verbose_name="Matriz",
    )
    loja = models.ForeignKey(
        Loja,
        on_delete=models.PROTECT,
        related_name="regras_fiscais",
        null=True,
        blank=True,
        verbose_name="Loja",
    )
    regime_tributario = models.CharField(
        "Regime tributario",
        max_length=12,
        choices=REGIME_TRIBUTARIO_CHOICES,
        default=REGIME_TODOS,
        db_index=True,
    )

    tipo_operacao = models.CharField(
        "Tipo de operacao",
        max_length=10,
        choices=TIPO_OPERACAO_CHOICES,
        default=TIPO_AMBOS,
        db_index=True,
    )
    finalidade_operacao = models.CharField(
        "Finalidade da operacao",
        max_length=16,
        choices=FINALIDADE_OPERACAO_CHOICES,
        db_index=True,
    )
    uf_origem = models.CharField(
        "UF de origem",
        max_length=2,
        blank=True,
        db_index=True,
    )
    uf_destino = models.CharField(
        "UF de destino",
        max_length=2,
        blank=True,
        db_index=True,
    )
    contribuinte_icms = models.BooleanField(
        "Contribuinte de ICMS",
        null=True,
        blank=True,
    )
    consumidor_final = models.BooleanField(
        "Consumidor final",
        null=True,
        blank=True,
    )

    ncm = models.ForeignKey(
        "fiscal.NCM",
        on_delete=models.PROTECT,
        related_name="regras_fiscais",
        null=True,
        blank=True,
        verbose_name="NCM",
    )
    cest = models.ForeignKey(
        "fiscal.CEST",
        on_delete=models.PROTECT,
        related_name="regras_fiscais",
        null=True,
        blank=True,
        verbose_name="CEST",
    )
    cfop = models.ForeignKey(
        "fiscal.CFOP",
        on_delete=models.PROTECT,
        related_name="regras_fiscais",
        null=True,
        blank=True,
        verbose_name="CFOP",
    )

    cst_icms = models.ForeignKey(
        "fiscal.CSTICMS",
        on_delete=models.PROTECT,
        related_name="regras_fiscais",
        null=True,
        blank=True,
        verbose_name="CST ICMS",
    )
    csosn = models.ForeignKey(
        "fiscal.CSOSN",
        on_delete=models.PROTECT,
        related_name="regras_fiscais",
        null=True,
        blank=True,
        verbose_name="CSOSN",
    )
    cst_pis = models.ForeignKey(
        "fiscal.CSTPIS",
        on_delete=models.PROTECT,
        related_name="regras_fiscais",
        null=True,
        blank=True,
        verbose_name="CST PIS",
    )
    cst_cofins = models.ForeignKey(
        "fiscal.CSTCOFINS",
        on_delete=models.PROTECT,
        related_name="regras_fiscais",
        null=True,
        blank=True,
        verbose_name="CST COFINS",
    )
    cst_ipi = models.ForeignKey(
        "fiscal.CSTIPI",
        on_delete=models.PROTECT,
        related_name="regras_fiscais",
        null=True,
        blank=True,
        verbose_name="CST IPI",
    )
    beneficio_fiscal = models.ForeignKey(
        "fiscal.BeneficioFiscal",
        on_delete=models.PROTECT,
        related_name="regras_fiscais",
        null=True,
        blank=True,
        verbose_name="Beneficio fiscal",
    )

    aliquota_icms = models.DecimalField(
        "Aliquota de ICMS",
        max_digits=9,
        decimal_places=4,
        null=True,
        blank=True,
    )
    reducao_base_icms = models.DecimalField(
        "Reducao da base de ICMS",
        max_digits=9,
        decimal_places=4,
        null=True,
        blank=True,
    )
    aliquota_fcp = models.DecimalField(
        "Aliquota de FCP",
        max_digits=9,
        decimal_places=4,
        null=True,
        blank=True,
    )
    aliquota_mva = models.DecimalField(
        "Aliquota de MVA",
        max_digits=9,
        decimal_places=4,
        null=True,
        blank=True,
    )
    aliquota_pis = models.DecimalField(
        "Aliquota de PIS",
        max_digits=9,
        decimal_places=4,
        null=True,
        blank=True,
    )
    aliquota_cofins = models.DecimalField(
        "Aliquota de COFINS",
        max_digits=9,
        decimal_places=4,
        null=True,
        blank=True,
    )
    aliquota_ipi = models.DecimalField(
        "Aliquota de IPI",
        max_digits=9,
        decimal_places=4,
        null=True,
        blank=True,
    )
    diferimento_icms = models.DecimalField(
        "Diferimento de ICMS",
        max_digits=9,
        decimal_places=4,
        null=True,
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
    criado_em = models.DateTimeField(
        "Criado em",
        auto_now_add=True,
    )
    atualizado_em = models.DateTimeField(
        "Atualizado em",
        auto_now=True,
    )

    class Meta:
        db_table = "fiscal_regra_fiscal"
        verbose_name = "Regra fiscal"
        verbose_name_plural = "Regras fiscais"
        ordering = (
            "prioridade",
            "codigo_interno",
        )
        indexes = [
            models.Index(
                fields=("ativo", "prioridade"),
                name="fiscal_reg_ativo_prio_idx",
            ),
            models.Index(
                fields=(
                    "regime_tributario",
                    "tipo_operacao",
                    "finalidade_operacao",
                ),
                name="fiscal_reg_reg_tipo_fin_idx",
            ),
            models.Index(
                fields=("uf_origem", "uf_destino"),
                name="fiscal_reg_ufs_idx",
            ),
            models.Index(
                fields=("matriz", "loja", "ativo"),
                name="fiscal_reg_escopo_idx",
            ),
        ]
        constraints = [
            models.CheckConstraint(
                condition=(
                    Q(cst_icms__isnull=True)
                    | Q(csosn__isnull=True)
                ),
                name="fiscal_reg_sem_cst_csosn_juntos",
            ),
        ]

    @staticmethod
    def normalizar_codigo(codigo):
        return (codigo or "").strip().upper()

    @staticmethod
    def normalizar_uf(uf):
        return (uf or "").strip().upper()

    def possui_condicao(self):
        return any(
            (
                self.matriz_id,
                self.loja_id,
                self.regime_tributario
                != self.REGIME_TODOS,
                self.tipo_operacao != self.TIPO_AMBOS,
                bool(self.finalidade_operacao),
                bool(self.uf_origem),
                bool(self.uf_destino),
                self.contribuinte_icms is not None,
                self.consumidor_final is not None,
                self.ncm_id,
                self.cest_id,
                self.cfop_id,
            )
        )

    def possui_resultado(self):
        return any(
            (
                self.cst_icms_id,
                self.csosn_id,
                self.cst_pis_id,
                self.cst_cofins_id,
                self.cst_ipi_id,
                self.beneficio_fiscal_id,
                self.aliquota_icms is not None,
                self.reducao_base_icms is not None,
                self.aliquota_fcp is not None,
                self.aliquota_mva is not None,
                self.aliquota_pis is not None,
                self.aliquota_cofins is not None,
                self.aliquota_ipi is not None,
                self.diferimento_icms is not None,
            )
        )

    def especificidade(self):
        campos = (
            self.loja_id,
            self.matriz_id,
            self.ncm_id,
            self.cest_id,
            self.cfop_id,
            bool(self.uf_origem),
            bool(self.uf_destino),
            self.regime_tributario
            != self.REGIME_TODOS,
            self.tipo_operacao != self.TIPO_AMBOS,
            self.contribuinte_icms is not None,
            self.consumidor_final is not None,
        )
        return sum(bool(valor) for valor in campos)

    def clean(self):
        erros = {}

        self.nome = (self.nome or "").strip()
        self.codigo_interno = self.normalizar_codigo(
            self.codigo_interno
        )
        self.descricao = (self.descricao or "").strip()
        self.uf_origem = self.normalizar_uf(
            self.uf_origem
        )
        self.uf_destino = self.normalizar_uf(
            self.uf_destino
        )

        if not self.nome:
            erros["nome"] = "Informe o nome da regra fiscal."

        if not self.codigo_interno:
            erros["codigo_interno"] = (
                "Informe o codigo interno da regra fiscal."
            )

        if self.loja_id:
            if not self.matriz_id:
                erros["matriz"] = (
                    "Informe a matriz da loja selecionada."
                )
            elif self.loja.matriz_id != self.matriz_id:
                erros["loja"] = (
                    "A loja deve pertencer a matriz selecionada."
                )

        for campo in ("uf_origem", "uf_destino"):
            valor = getattr(self, campo)
            if valor and valor not in UFS_VALIDAS:
                erros[campo] = "Informe uma UF valida."

        if self.cst_icms_id and self.csosn_id:
            erros["csosn"] = (
                "CST ICMS e CSOSN nao podem coexistir."
            )

        if (
            self.regime_tributario
            in {self.REGIME_SIMPLES, self.REGIME_MEI}
            and self.cst_icms_id
        ):
            erros["cst_icms"] = (
                "Regra do Simples ou MEI deve utilizar CSOSN."
            )

        if (
            self.regime_tributario == self.REGIME_NORMAL
            and self.csosn_id
        ):
            erros["csosn"] = (
                "Regra do regime normal deve utilizar CST ICMS."
            )

        for campo in (
            "aliquota_icms",
            "reducao_base_icms",
            "aliquota_fcp",
            "aliquota_pis",
            "aliquota_cofins",
            "aliquota_ipi",
            "diferimento_icms",
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
            self.aliquota_mva is not None
            and self.aliquota_mva < Decimal("0")
        ):
            erros["aliquota_mva"] = (
                "A MVA nao pode ser negativa."
            )

        if (
            self.vigencia_inicio
            and self.vigencia_fim
            and self.vigencia_fim < self.vigencia_inicio
        ):
            erros["vigencia_fim"] = (
                "O fim da vigencia nao pode ser anterior ao inicio."
            )

        for campo in (
            "ncm",
            "cest",
            "cfop",
            "cst_icms",
            "csosn",
            "cst_pis",
            "cst_cofins",
            "cst_ipi",
            "beneficio_fiscal",
        ):
            objeto = getattr(self, campo, None)
            if objeto is not None and not objeto.ativo:
                erros[campo] = (
                    "O cadastro fiscal selecionado deve estar ativo."
                )

        if self.ativo and not self.possui_condicao():
            erros["finalidade_operacao"] = (
                "A regra ativa precisa possuir ao menos uma condicao."
            )

        if not self.possui_resultado():
            erros["cst_icms"] = (
                "Informe ao menos um resultado tributario."
            )

        if erros:
            raise ValidationError(erros)

    def save(self, *args, **kwargs):
        self.codigo_interno = self.normalizar_codigo(
            self.codigo_interno
        )
        self.nome = (self.nome or "").strip()
        self.descricao = (self.descricao or "").strip()
        self.uf_origem = self.normalizar_uf(
            self.uf_origem
        )
        self.uf_destino = self.normalizar_uf(
            self.uf_destino
        )
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return (
            f"{self.codigo_interno} - {self.nome} "
            f"(prioridade {self.prioridade})"
        )
