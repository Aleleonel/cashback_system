from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("fiscal", "0018_seed_cest_homologacao"),
    ]

    operations = [
        migrations.CreateModel(
            name="BeneficioFiscal",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("codigo", models.CharField(db_index=True, max_length=20, unique=True, verbose_name="Codigo")),
                ("descricao", models.TextField(verbose_name="Descricao")),
                ("uf", models.CharField(blank=True, db_index=True, max_length=2, verbose_name="UF")),
                (
                    "tipo_beneficio",
                    models.CharField(
                        choices=[
                            ("isencao", "Isencao"),
                            ("reducao_base", "Reducao de base"),
                            ("diferimento", "Diferimento"),
                            ("credito_presumido", "Credito presumido"),
                            ("desoneracao", "Desoneracao"),
                            ("imunidade", "Imunidade"),
                            ("suspensao", "Suspensao"),
                            ("outros", "Outros"),
                        ],
                        db_index=True,
                        max_length=24,
                        verbose_name="Tipo de beneficio",
                    ),
                ),
                ("fundamento_legal", models.TextField(blank=True, verbose_name="Fundamento legal")),
                ("percentual_reducao", models.DecimalField(blank=True, decimal_places=4, max_digits=7, null=True, verbose_name="Percentual de reducao")),
                ("percentual_credito", models.DecimalField(blank=True, decimal_places=4, max_digits=7, null=True, verbose_name="Percentual de credito")),
                ("exige_motivo_desoneracao", models.BooleanField(default=False, verbose_name="Exige motivo de desoneracao")),
                ("motivo_desoneracao_padrao", models.CharField(blank=True, max_length=2, verbose_name="Motivo de desoneracao padrao")),
                (
                    "regime_tributario",
                    models.CharField(
                        choices=[
                            ("todos", "Todos"),
                            ("normal", "Regime normal"),
                            ("simples", "Simples Nacional"),
                            ("mei", "MEI"),
                        ],
                        db_index=True,
                        default="todos",
                        max_length=12,
                        verbose_name="Regime tributario",
                    ),
                ),
                ("vigencia_inicio", models.DateField(blank=True, null=True, verbose_name="Inicio da vigencia")),
                ("vigencia_fim", models.DateField(blank=True, null=True, verbose_name="Fim da vigencia")),
                ("ativo", models.BooleanField(db_index=True, default=True, verbose_name="Ativo")),
                ("criado_em", models.DateTimeField(auto_now_add=True, verbose_name="Criado em")),
                ("atualizado_em", models.DateTimeField(auto_now=True, verbose_name="Atualizado em")),
            ],
            options={
                "verbose_name": "Beneficio fiscal",
                "verbose_name_plural": "Beneficios fiscais",
                "db_table": "fiscal_beneficio_fiscal",
                "ordering": ("codigo",),
                "indexes": [
                    models.Index(fields=["ativo", "codigo"], name="fiscal_ben_ativo_cod_idx"),
                    models.Index(fields=["uf", "tipo_beneficio"], name="fiscal_ben_uf_tipo_idx"),
                    models.Index(fields=["regime_tributario", "ativo"], name="fiscal_ben_reg_ativo_idx"),
                ],
            },
        ),
    ]
