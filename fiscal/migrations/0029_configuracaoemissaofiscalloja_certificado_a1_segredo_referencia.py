from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("fiscal", "0028_documentofiscal_numero_recibo_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="configuracaoemissaofiscalloja",
            name="certificado_a1_segredo_referencia",
            field=models.CharField(
                blank=True,
                default="",
                help_text=(
                    "Referencia opaca do secret da senha A1. "
                    "Nunca armazene a senha neste campo."
                ),
                max_length=500,
            ),
        ),
    ]
