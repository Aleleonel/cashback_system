from django.db import migrations

CSOSNS = (
    ("101", "Tributada pelo Simples Nacional com permissao de credito", True, True, False, False),
    ("102", "Tributada pelo Simples Nacional sem permissao de credito", True, False, False, False),
    ("103", "Isencao do ICMS no Simples Nacional para faixa de receita bruta", False, False, False, False),
    ("201", "Tributada pelo Simples Nacional com permissao de credito e cobranca por substituicao tributaria", True, True, False, True),
    ("202", "Tributada pelo Simples Nacional sem permissao de credito e cobranca por substituicao tributaria", True, False, False, True),
    ("203", "Isencao do ICMS no Simples Nacional para faixa de receita bruta e cobranca por substituicao tributaria", False, False, False, True),
    ("300", "Imune", False, False, False, False),
    ("400", "Nao tributada pelo Simples Nacional", False, False, False, False),
    ("500", "ICMS cobrado anteriormente por substituicao tributaria ou antecipacao", False, False, False, True),
    ("900", "Outros", False, False, False, False),
)

def carregar(apps, schema_editor):
    Model = apps.get_model("fiscal", "CSOSN")
    for codigo, descricao, aliquota, credito, reducao, st in CSOSNS:
        Model.objects.update_or_create(
            codigo=codigo,
            defaults={
                "descricao": descricao,
                "exige_aliquota": aliquota,
                "permite_credito": credito,
                "permite_reducao_base": reducao,
                "permite_substituicao_tributaria": st,
                "ativo": True,
            },
        )

def remover(apps, schema_editor):
    Model = apps.get_model("fiscal", "CSOSN")
    Model.objects.filter(codigo__in=[item[0] for item in CSOSNS]).delete()

class Migration(migrations.Migration):
    dependencies = [("fiscal", "0005_csosn")]
    operations = [migrations.RunPython(carregar, remover)]
