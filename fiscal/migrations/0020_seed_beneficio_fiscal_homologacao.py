from django.db import migrations


REGISTROS = (
    (
        "BEN-HOM-001",
        "Beneficio de homologacao para isencao",
        "",
        "isencao",
        "todos",
        None,
        None,
        False,
        "",
    ),
    (
        "BEN-HOM-002",
        "Beneficio de homologacao para reducao de base",
        "SP",
        "reducao_base",
        "normal",
        "30.0000",
        None,
        False,
        "",
    ),
    (
        "BEN-HOM-003",
        "Beneficio de homologacao para diferimento",
        "MG",
        "diferimento",
        "normal",
        None,
        None,
        False,
        "",
    ),
    (
        "BEN-HOM-004",
        "Beneficio de homologacao para credito presumido",
        "PR",
        "credito_presumido",
        "normal",
        None,
        "5.0000",
        False,
        "",
    ),
    (
        "BEN-HOM-005",
        "Beneficio de homologacao para desoneracao",
        "RJ",
        "desoneracao",
        "todos",
        None,
        None,
        True,
        "9",
    ),
    (
        "BEN-HOM-006",
        "Beneficio de homologacao para suspensao",
        "",
        "suspensao",
        "simples",
        None,
        None,
        False,
        "",
    ),
)


def carregar(apps, schema_editor):
    Model = apps.get_model(
        "fiscal",
        "BeneficioFiscal",
    )

    for (
        codigo,
        descricao,
        uf,
        tipo,
        regime,
        reducao,
        credito,
        exige_motivo,
        motivo,
    ) in REGISTROS:
        Model.objects.update_or_create(
            codigo=codigo,
            defaults={
                "descricao": descricao,
                "uf": uf,
                "tipo_beneficio": tipo,
                "regime_tributario": regime,
                "percentual_reducao": reducao,
                "percentual_credito": credito,
                "exige_motivo_desoneracao": exige_motivo,
                "motivo_desoneracao_padrao": motivo,
                "fundamento_legal": (
                    "Registro de homologacao. "
                    "Nao utilizar em emissao fiscal real."
                ),
                "ativo": True,
            },
        )


def remover(apps, schema_editor):
    Model = apps.get_model(
        "fiscal",
        "BeneficioFiscal",
    )
    Model.objects.filter(
        codigo__in=[item[0] for item in REGISTROS]
    ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("fiscal", "0019_beneficio_fiscal"),
    ]

    operations = [
        migrations.RunPython(
            carregar,
            remover,
        ),
    ]
