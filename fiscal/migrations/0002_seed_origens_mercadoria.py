from django.db import migrations


ORIGENS = (
    (
        "0",
        "Nacional, exceto as indicadas nos codigos 3, 4, 5 e 8",
    ),
    (
        "1",
        "Estrangeira - importacao direta, exceto a indicada no codigo 6",
    ),
    (
        "2",
        "Estrangeira - adquirida no mercado interno, exceto a indicada no codigo 7",
    ),
    (
        "3",
        "Nacional, mercadoria ou bem com conteudo de importacao superior a 40% e inferior ou igual a 70%",
    ),
    (
        "4",
        "Nacional, producao em conformidade com processos produtivos basicos",
    ),
    (
        "5",
        "Nacional, mercadoria ou bem com conteudo de importacao inferior ou igual a 40%",
    ),
    (
        "6",
        "Estrangeira - importacao direta, sem similar nacional, constante em lista da CAMEX",
    ),
    (
        "7",
        "Estrangeira - adquirida no mercado interno, sem similar nacional, constante em lista da CAMEX",
    ),
    (
        "8",
        "Nacional, mercadoria ou bem com conteudo de importacao superior a 70%",
    ),
)


def carregar_origens(apps, schema_editor):
    OrigemMercadoria = apps.get_model(
        "fiscal",
        "OrigemMercadoria",
    )

    for codigo, descricao in ORIGENS:
        OrigemMercadoria.objects.update_or_create(
            codigo=codigo,
            defaults={
                "descricao": descricao,
                "ativo": True,
            },
        )


def remover_origens(apps, schema_editor):
    OrigemMercadoria = apps.get_model(
        "fiscal",
        "OrigemMercadoria",
    )
    OrigemMercadoria.objects.filter(
        codigo__in=[codigo for codigo, _ in ORIGENS]
    ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("fiscal", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(
            carregar_origens,
            remover_origens,
        ),
    ]
