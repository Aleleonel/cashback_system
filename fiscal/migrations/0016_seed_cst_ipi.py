from django.db import migrations


ENTRADA = "entrada"
SAIDA = "saida"


CSTS = (
    ("00", "Entrada com recuperacao de credito", ENTRADA, True, True, True, True, True),
    ("01", "Entrada tributada com aliquota zero", ENTRADA, False, False, False, False, True),
    ("02", "Entrada isenta", ENTRADA, False, False, False, False, True),
    ("03", "Entrada nao tributada", ENTRADA, False, False, False, False, True),
    ("04", "Entrada imune", ENTRADA, False, False, False, False, True),
    ("05", "Entrada com suspensao", ENTRADA, False, False, False, False, True),
    ("49", "Outras entradas", ENTRADA, False, False, False, False, True),
    ("50", "Saida tributada", SAIDA, True, True, False, True, True),
    ("51", "Saida tributada com aliquota zero", SAIDA, False, False, False, False, True),
    ("52", "Saida isenta", SAIDA, False, False, False, False, True),
    ("53", "Saida nao tributada", SAIDA, False, False, False, False, True),
    ("54", "Saida imune", SAIDA, False, False, False, False, True),
    ("55", "Saida com suspensao", SAIDA, False, False, False, False, True),
    ("99", "Outras saidas", SAIDA, False, False, False, False, True),
)


def carregar(apps, schema_editor):
    Model = apps.get_model("fiscal", "CSTIPI")

    for (
        codigo,
        descricao,
        tipo,
        tributado,
        aliquota,
        credito,
        base,
        enquadramento,
    ) in CSTS:
        Model.objects.update_or_create(
            codigo=codigo,
            defaults={
                "descricao": descricao,
                "tipo_operacao": tipo,
                "tributado": tributado,
                "exige_aliquota": aliquota,
                "permite_credito": credito,
                "exige_base_calculo": base,
                "exige_codigo_enquadramento": enquadramento,
                "ativo": True,
            },
        )


def remover(apps, schema_editor):
    Model = apps.get_model("fiscal", "CSTIPI")
    Model.objects.filter(
        codigo__in=[item[0] for item in CSTS]
    ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("fiscal", "0015_cst_ipi"),
    ]

    operations = [
        migrations.RunPython(
            carregar,
            remover,
        ),
    ]
