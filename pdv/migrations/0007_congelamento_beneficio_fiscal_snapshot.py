from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("pdv", "0006_venda_uf_destino"),
    ]

    operations = [
        migrations.AddField(
            model_name="itemvendafiscal",
            name="beneficio_fiscal_tipo",
            field=models.CharField(
                blank=True,
                default="",
                max_length=30,
            ),
        ),
        migrations.AddField(
            model_name="itemvendafiscal",
            name="beneficio_exige_motivo_desoneracao",
            field=models.BooleanField(
                default=False,
            ),
        ),
        migrations.AddField(
            model_name="itemvendafiscal",
            name="beneficio_motivo_desoneracao",
            field=models.CharField(
                blank=True,
                default="",
                max_length=2,
            ),
        ),
    ]