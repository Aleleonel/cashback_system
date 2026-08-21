from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("fiscal", "0025_parametrizar_cfop_regra_homologacao_venda"),
    ]

    operations = [
        migrations.CreateModel(
            name="ConfiguracaoEmissaoFiscalLoja",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("razao_social", models.CharField(max_length=150)),
                ("nome_fantasia", models.CharField(blank=True, default="", max_length=150)),
                ("inscricao_estadual", models.CharField(max_length=20)),
                ("logradouro", models.CharField(max_length=150)),
                ("numero", models.CharField(max_length=20)),
                ("complemento", models.CharField(blank=True, default="", max_length=100)),
                ("bairro", models.CharField(max_length=100)),
                ("municipio", models.CharField(max_length=100)),
                ("codigo_municipio_ibge", models.CharField(max_length=7)),
                ("uf", models.CharField(max_length=2)),
                ("cep", models.CharField(max_length=8)),
                ("crt", models.CharField(max_length=2)),
                ("ambiente_nfce", models.CharField(choices=[("homologacao", "Homologacao"), ("producao", "Producao")], default="homologacao", max_length=20)),
                ("serie_nfce", models.PositiveSmallIntegerField(default=1)),
                ("ativa", models.BooleanField(default=True)),
                ("criado_em", models.DateTimeField(auto_now_add=True)),
                ("atualizado_em", models.DateTimeField(auto_now=True)),
                ("loja", models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name="configuracao_emissao_fiscal", to="empresas.loja")),
            ],
            options={
                "verbose_name": "configuracao de emissao fiscal da loja",
                "verbose_name_plural": "configurações de emissao fiscal das lojas",
                "ordering": ("loja_id",),
            },
        ),
    ]
