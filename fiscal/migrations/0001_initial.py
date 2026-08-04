from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="OrigemMercadoria",
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
                        max_length=1,
                        unique=True,
                        validators=[
                            django.core.validators.RegexValidator(
                                message=(
                                    "O codigo deve ser um digito "
                                    "entre 0 e 8."
                                ),
                                regex="^[0-8]$",
                            )
                        ],
                        verbose_name="Codigo",
                    ),
                ),
                (
                    "descricao",
                    models.CharField(
                        max_length=180,
                        verbose_name="Descricao",
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
                "verbose_name": "Origem da mercadoria",
                "verbose_name_plural": "Origens da mercadoria",
                "db_table": "fiscal_origem_mercadoria",
                "ordering": ("codigo",),
                "indexes": [
                    models.Index(
                        fields=["ativo", "codigo"],
                        name="fiscal_orig_ativo_cod_idx",
                    )
                ],
            },
        ),
    ]
