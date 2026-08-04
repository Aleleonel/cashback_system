from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):
    dependencies = [
        ("fiscal", "0014_seed_cst_cofins"),
    ]

    operations = [
        migrations.CreateModel(
            name="CSTIPI",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "codigo",
                    models.CharField(
                        db_index=True,
                        max_length=2,
                        unique=True,
                        validators=[
                            django.core.validators.RegexValidator(
                                message="O codigo deve conter exatamente dois digitos.",
                                regex=r"^\d{2}$",
                            )
                        ],
                        verbose_name="Codigo",
                    ),
                ),
                ("descricao", models.CharField(max_length=240, verbose_name="Descricao")),
                (
                    "tipo_operacao",
                    models.CharField(
                        choices=[
                            ("entrada", "Entrada"),
                            ("saida", "Saida"),
                            ("ambos", "Entrada e saida"),
                        ],
                        db_index=True,
                        max_length=10,
                        verbose_name="Tipo de operacao",
                    ),
                ),
                ("tributado", models.BooleanField(default=False, verbose_name="Operacao tributada")),
                ("exige_aliquota", models.BooleanField(default=False, verbose_name="Exige aliquota")),
                ("permite_credito", models.BooleanField(default=False, verbose_name="Permite credito")),
                ("exige_base_calculo", models.BooleanField(default=False, verbose_name="Exige base de calculo")),
                ("exige_codigo_enquadramento", models.BooleanField(default=False, verbose_name="Exige codigo de enquadramento")),
                ("ativo", models.BooleanField(db_index=True, default=True, verbose_name="Ativo")),
                ("criado_em", models.DateTimeField(auto_now_add=True, verbose_name="Criado em")),
                ("atualizado_em", models.DateTimeField(auto_now=True, verbose_name="Atualizado em")),
            ],
            options={
                "verbose_name": "CST IPI",
                "verbose_name_plural": "CST IPI",
                "db_table": "fiscal_cst_ipi",
                "ordering": ("codigo",),
                "indexes": [
                    models.Index(fields=["ativo", "codigo"], name="fiscal_cstipi_ativo_cod_idx"),
                    models.Index(fields=["tipo_operacao", "ativo"], name="fiscal_cstipi_tipo_ativo_idx"),
                ],
            },
        ),
    ]
