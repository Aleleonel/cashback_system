from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):
    dependencies = [
        ("fiscal", "0016_seed_cst_ipi"),
    ]

    operations = [
        migrations.CreateModel(
            name="CEST",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "codigo",
                    models.CharField(
                        db_index=True,
                        max_length=7,
                        unique=True,
                        validators=[
                            django.core.validators.RegexValidator(
                                message="O codigo deve conter exatamente sete digitos.",
                                regex=r"^\d{7}$",
                            )
                        ],
                        verbose_name="Codigo",
                    ),
                ),
                ("descricao", models.TextField(verbose_name="Descricao")),
                ("segmento", models.CharField(blank=True, db_index=True, max_length=160, verbose_name="Segmento")),
                ("ncm_referencia", models.CharField(blank=True, db_index=True, max_length=8, verbose_name="NCM de referencia")),
                ("excecao", models.CharField(blank=True, max_length=120, verbose_name="Excecao")),
                ("versao_tabela", models.CharField(blank=True, max_length=40, verbose_name="Versao da tabela")),
                ("vigencia_inicio", models.DateField(blank=True, null=True, verbose_name="Inicio da vigencia")),
                ("vigencia_fim", models.DateField(blank=True, null=True, verbose_name="Fim da vigencia")),
                ("ativo", models.BooleanField(db_index=True, default=True, verbose_name="Ativo")),
                ("criado_em", models.DateTimeField(auto_now_add=True, verbose_name="Criado em")),
                ("atualizado_em", models.DateTimeField(auto_now=True, verbose_name="Atualizado em")),
            ],
            options={
                "verbose_name": "CEST",
                "verbose_name_plural": "CEST",
                "db_table": "fiscal_cest",
                "ordering": ("codigo",),
                "indexes": [
                    models.Index(fields=["ativo", "codigo"], name="fiscal_cest_ativo_cod_idx"),
                    models.Index(fields=["segmento", "ativo"], name="fiscal_cest_seg_ativo_idx"),
                    models.Index(fields=["ncm_referencia", "ativo"], name="fiscal_cest_ncm_ativo_idx"),
                ],
            },
        ),
    ]
