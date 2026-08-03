from django.db import migrations


REGISTROS = (
    ("0100100", "Registro CEST de homologacao 1", "Homologacao", "21069030"),
    ("0200200", "Registro CEST de homologacao 2", "Homologacao", "22021000"),
    ("0300300", "Registro CEST de homologacao 3", "Homologacao", "33049990"),
    ("0400400", "Registro CEST de homologacao 4", "Homologacao", "39241000"),
    ("0500500", "Registro CEST de homologacao 5", "Homologacao", "48181000"),
    ("0600600", "Registro CEST de homologacao 6", "Homologacao", "85171231"),
)


def carregar(apps, schema_editor):
    Model = apps.get_model("fiscal", "CEST")

    for codigo, descricao, segmento, ncm in REGISTROS:
        Model.objects.update_or_create(
            codigo=codigo,
            defaults={
                "descricao": descricao,
                "segmento": segmento,
                "ncm_referencia": ncm,
                "versao_tabela": "homologacao-1",
                "ativo": True,
            },
        )


def remover(apps, schema_editor):
    Model = apps.get_model("fiscal", "CEST")
    Model.objects.filter(
        codigo__in=[item[0] for item in REGISTROS]
    ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("fiscal", "0017_cest"),
    ]

    operations = [
        migrations.RunPython(
            carregar,
            remover,
        ),
    ]
