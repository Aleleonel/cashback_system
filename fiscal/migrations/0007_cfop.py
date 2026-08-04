from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):
    dependencies = [("fiscal", "0006_seed_csosn")]

    operations = [
        migrations.CreateModel(
            name="CFOP",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("codigo", models.CharField(
                    db_index=True,
                    max_length=4,
                    unique=True,
                    validators=[django.core.validators.RegexValidator(
                        message="O codigo deve conter quatro digitos e iniciar por 1, 2, 3, 5, 6 ou 7.",
                        regex=r"^[123567]\d{3}$",
                    )],
                    verbose_name="Codigo",
                )),
                ("descricao", models.CharField(max_length=260, verbose_name="Descricao")),
                ("tipo_operacao", models.CharField(
                    choices=[("entrada", "Entrada"), ("saida", "Saida")],
                    db_index=True,
                    editable=False,
                    max_length=10,
                    verbose_name="Tipo de operacao",
                )),
                ("destino_operacao", models.CharField(
                    choices=[("interna", "Interna"), ("interestadual", "Interestadual"), ("exterior", "Exterior")],
                    db_index=True,
                    editable=False,
                    max_length=15,
                    verbose_name="Destino da operacao",
                )),
                ("gera_movimento_estoque", models.BooleanField(default=True, verbose_name="Gera movimento de estoque")),
                ("permite_devolucao", models.BooleanField(default=False, verbose_name="Permite devolucao")),
                ("permite_remessa", models.BooleanField(default=False, verbose_name="Permite remessa")),
                ("ativo", models.BooleanField(db_index=True, default=True, verbose_name="Ativo")),
                ("criado_em", models.DateTimeField(auto_now_add=True, verbose_name="Criado em")),
                ("atualizado_em", models.DateTimeField(auto_now=True, verbose_name="Atualizado em")),
            ],
            options={
                "verbose_name": "CFOP",
                "verbose_name_plural": "CFOP",
                "db_table": "fiscal_cfop",
                "ordering": ("codigo",),
                "indexes": [
                    models.Index(fields=["ativo", "codigo"], name="fiscal_cfop_ativo_cod_idx"),
                    models.Index(fields=["tipo_operacao", "destino_operacao"], name="fiscal_cfop_tipo_dest_idx"),
                ],
            },
        ),
    ]
