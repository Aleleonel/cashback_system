from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):
    dependencies = [
        ("fiscal", "0008_seed_cfop"),
    ]

    operations = [
        migrations.CreateModel(
            name="NCM",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "codigo",
                    models.CharField(
                        db_index=True,
                        max_length=8,
                        unique=True,
                        validators=[
                            django.core.validators.RegexValidator(
                                message="O codigo deve conter exatamente oito digitos.",
                                regex=r"^\d{8}$",
                            )
                        ],
                        verbose_name="Codigo",
                    ),
                ),
                (
                    "descricao",
                    models.TextField(
                        verbose_name="Descricao",
                    ),
                ),
                (
                    "unidade_tributavel_padrao",
                    models.CharField(
                        blank=True,
                        max_length=10,
                        verbose_name="Unidade tributavel padrao",
                    ),
                ),
                (
                    "ativo",
                    models.BooleanField(
                        db_index=True,
                        default=True,
                        verbose_name="Ativo",
                    ),
                ),
                (
                    "criado_em",
                    models.DateTimeField(
                        auto_now_add=True,
                        verbose_name="Criado em",
                    ),
                ),
                (
                    "atualizado_em",
                    models.DateTimeField(
                        auto_now=True,
                        verbose_name="Atualizado em",
                    ),
                ),
            ],
            options={
                "verbose_name": "NCM",
                "verbose_name_plural": "NCM",
                "db_table": "fiscal_ncm",
                "ordering": ("codigo",),
                "indexes": [
                    models.Index(
                        fields=["ativo", "codigo"],
                        name="fiscal_ncm_ativo_cod_idx",
                    )
                ],
            },
        ),
    ]
