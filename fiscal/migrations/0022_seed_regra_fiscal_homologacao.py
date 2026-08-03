from django.db import migrations


CODIGOS = (
    "REG-HOM-VENDA-SP",
    "REG-HOM-COMPRA-SP",
)


def carregar(apps, schema_editor):
    RegraFiscal = apps.get_model(
        "fiscal",
        "RegraFiscal",
    )
    CSTICMS = apps.get_model(
        "fiscal",
        "CSTICMS",
    )
    CSTPIS = apps.get_model(
        "fiscal",
        "CSTPIS",
    )
    CSTCOFINS = apps.get_model(
        "fiscal",
        "CSTCOFINS",
    )

    cst_icms = CSTICMS.objects.filter(
        codigo="00",
        ativo=True,
    ).first()
    cst_pis = CSTPIS.objects.filter(
        codigo="01",
        ativo=True,
    ).first()
    cst_cofins = CSTCOFINS.objects.filter(
        codigo="01",
        ativo=True,
    ).first()

    if not cst_icms:
        return

    RegraFiscal.objects.update_or_create(
        codigo_interno="REG-HOM-VENDA-SP",
        defaults={
            "nome": "Regra de homologacao - venda SP",
            "descricao": (
                "Registro exclusivo de homologacao. "
                "Nao utilizar em emissao fiscal real."
            ),
            "prioridade": 900,
            "ativo": True,
            "regime_tributario": "normal",
            "tipo_operacao": "saida",
            "finalidade_operacao": "venda",
            "uf_origem": "SP",
            "uf_destino": "SP",
            "cst_icms": cst_icms,
            "cst_pis": cst_pis,
            "cst_cofins": cst_cofins,
        },
    )

    RegraFiscal.objects.update_or_create(
        codigo_interno="REG-HOM-COMPRA-SP",
        defaults={
            "nome": "Regra de homologacao - compra SP",
            "descricao": (
                "Registro exclusivo de homologacao. "
                "Nao utilizar em operacao fiscal real."
            ),
            "prioridade": 900,
            "ativo": True,
            "regime_tributario": "normal",
            "tipo_operacao": "entrada",
            "finalidade_operacao": "compra",
            "uf_origem": "SP",
            "uf_destino": "SP",
            "cst_icms": cst_icms,
        },
    )


def remover(apps, schema_editor):
    RegraFiscal = apps.get_model(
        "fiscal",
        "RegraFiscal",
    )
    RegraFiscal.objects.filter(
        codigo_interno__in=CODIGOS
    ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("fiscal", "0021_regra_fiscal"),
    ]

    operations = [
        migrations.RunPython(
            carregar,
            remover,
        ),
    ]
