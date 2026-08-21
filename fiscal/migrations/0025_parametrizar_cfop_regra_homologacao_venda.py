from django.db import migrations


REGRA_CODIGO = "REG-HOM-VENDA-SP"
CFOP_CODIGO = "5102"


def aplicar(apps, schema_editor):
    RegraFiscal = apps.get_model("fiscal", "RegraFiscal")
    CFOP = apps.get_model("fiscal", "CFOP")

    regra = RegraFiscal.objects.filter(
        codigo_interno=REGRA_CODIGO
    ).first()
    if regra is None:
        raise RuntimeError(
            f"Regra fiscal de homologacao ausente: {REGRA_CODIGO}"
        )

    cfop = CFOP.objects.filter(
        codigo=CFOP_CODIGO,
        ativo=True,
    ).first()
    if cfop is None:
        raise RuntimeError(
            f"CFOP ativo de homologacao ausente: {CFOP_CODIGO}"
        )

    if regra.cfop_id is not None:
        if regra.cfop_id == cfop.pk:
            return
        raise RuntimeError(
            "REG-HOM-VENDA-SP ja possui CFOP diferente de 5102; "
            "migration abortada para evitar sobrescrita."
        )

    RegraFiscal.objects.filter(pk=regra.pk).update(
        cfop_id=cfop.pk
    )


def reverter(apps, schema_editor):
    RegraFiscal = apps.get_model("fiscal", "RegraFiscal")
    CFOP = apps.get_model("fiscal", "CFOP")

    cfop = CFOP.objects.filter(
        codigo=CFOP_CODIGO
    ).first()
    if cfop is None:
        return

    RegraFiscal.objects.filter(
        codigo_interno=REGRA_CODIGO,
        cfop_id=cfop.pk,
    ).update(
        cfop_id=None
    )


class Migration(migrations.Migration):
    dependencies = [
        ("fiscal", "0024_documento_fiscal_fundacao"),
    ]

    operations = [
        migrations.RunPython(
            aplicar,
            reverter,
        ),
    ]
