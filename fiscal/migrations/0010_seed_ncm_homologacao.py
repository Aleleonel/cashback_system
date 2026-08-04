from django.db import migrations


NCMS = (
    (
        "21069030",
        "Preparacoes alimenticias nao especificadas nem compreendidas em outras posicoes",
        "",
    ),
    (
        "21069090",
        "Outras preparacoes alimenticias",
        "",
    ),
    (
        "21061000",
        "Concentrados de proteinas e substancias proteicas texturizadas",
        "",
    ),
    (
        "21069010",
        "Preparacoes do tipo utilizado para elaboracao de bebidas",
        "",
    ),
    (
        "04041000",
        "Soro de leite, modificado ou nao",
        "",
    ),
    (
        "35022000",
        "Lactalbumina, incluindo concentrados de duas ou mais proteinas do soro do leite",
        "",
    ),
)


def carregar(apps, schema_editor):
    Model = apps.get_model("fiscal", "NCM")

    for codigo, descricao, unidade in NCMS:
        Model.objects.update_or_create(
            codigo=codigo,
            defaults={
                "descricao": descricao,
                "unidade_tributavel_padrao": unidade,
                "ativo": True,
            },
        )


def remover(apps, schema_editor):
    Model = apps.get_model("fiscal", "NCM")
    Model.objects.filter(
        codigo__in=[item[0] for item in NCMS]
    ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("fiscal", "0009_ncm"),
    ]

    operations = [
        migrations.RunPython(
            carregar,
            remover,
        ),
    ]
