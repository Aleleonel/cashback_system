from django.db import migrations

CSTS = (
    ("00", "Tributada integralmente", True, False, False, False),
    ("10", "Tributada e com cobranca do ICMS por substituicao tributaria", True, False, False, True),
    ("20", "Com reducao de base de calculo", True, True, False, False),
    ("30", "Isenta ou nao tributada e com cobranca do ICMS por substituicao tributaria", False, False, False, True),
    ("40", "Isenta", False, False, False, False),
    ("41", "Nao tributada", False, False, False, False),
    ("50", "Suspensao", False, False, False, False),
    ("51", "Diferimento", False, False, True, False),
    ("60", "ICMS cobrado anteriormente por substituicao tributaria", False, False, False, True),
    ("70", "Com reducao de base e cobranca do ICMS por substituicao tributaria", True, True, False, True),
    ("90", "Outras", False, False, False, False),
)

def carregar(apps, schema_editor):
    Model = apps.get_model("fiscal", "CSTICMS")
    for codigo, descricao, aliquota, reducao, diferimento, st in CSTS:
        Model.objects.update_or_create(codigo=codigo, defaults={"descricao": descricao, "exige_aliquota": aliquota, "permite_reducao_base": reducao, "permite_diferimento": diferimento, "permite_substituicao_tributaria": st, "ativo": True})

def remover(apps, schema_editor):
    Model = apps.get_model("fiscal", "CSTICMS")
    Model.objects.filter(codigo__in=[item[0] for item in CSTS]).delete()

class Migration(migrations.Migration):
    dependencies = [("fiscal", "0003_cst_icms")]
    operations = [migrations.RunPython(carregar, remover)]
