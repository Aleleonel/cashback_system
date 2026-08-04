from django.db import migrations


SAIDA = "saida"
ENTRADA = "entrada"
AMBOS = "ambos"

CSTS = (
    ("01", "Operacao tributavel com aliquota basica", SAIDA, True, True, False, True),
    ("02", "Operacao tributavel com aliquota diferenciada", SAIDA, True, True, False, True),
    ("03", "Operacao tributavel por unidade de medida de produto", SAIDA, True, True, False, True),
    ("04", "Operacao tributavel monofasica com aliquota zero", SAIDA, False, False, False, False),
    ("05", "Operacao tributavel por substituicao tributaria", SAIDA, True, True, False, True),
    ("06", "Operacao tributavel com aliquota zero", SAIDA, False, False, False, False),
    ("07", "Operacao isenta da contribuicao", SAIDA, False, False, False, False),
    ("08", "Operacao sem incidencia da contribuicao", SAIDA, False, False, False, False),
    ("09", "Operacao com suspensao da contribuicao", SAIDA, False, False, False, False),
    ("49", "Outras operacoes de saida", SAIDA, False, False, False, False),
    ("50", "Operacao com direito a credito vinculada exclusivamente a receita tributada no mercado interno", ENTRADA, False, False, True, True),
    ("51", "Operacao com direito a credito vinculada exclusivamente a receita nao tributada no mercado interno", ENTRADA, False, False, True, True),
    ("52", "Operacao com direito a credito vinculada exclusivamente a receita de exportacao", ENTRADA, False, False, True, True),
    ("53", "Operacao com direito a credito vinculada a receitas tributadas e nao tributadas no mercado interno", ENTRADA, False, False, True, True),
    ("54", "Operacao com direito a credito vinculada a receitas tributadas no mercado interno e de exportacao", ENTRADA, False, False, True, True),
    ("55", "Operacao com direito a credito vinculada a receitas nao tributadas no mercado interno e de exportacao", ENTRADA, False, False, True, True),
    ("56", "Operacao com direito a credito vinculada a receitas tributadas e nao tributadas no mercado interno e de exportacao", ENTRADA, False, False, True, True),
    ("60", "Credito presumido vinculado exclusivamente a receita tributada no mercado interno", ENTRADA, False, False, True, True),
    ("61", "Credito presumido vinculado exclusivamente a receita nao tributada no mercado interno", ENTRADA, False, False, True, True),
    ("62", "Credito presumido vinculado exclusivamente a receita de exportacao", ENTRADA, False, False, True, True),
    ("63", "Credito presumido vinculado a receitas tributadas e nao tributadas no mercado interno", ENTRADA, False, False, True, True),
    ("64", "Credito presumido vinculado a receitas tributadas no mercado interno e de exportacao", ENTRADA, False, False, True, True),
    ("65", "Credito presumido vinculado a receitas nao tributadas no mercado interno e de exportacao", ENTRADA, False, False, True, True),
    ("66", "Credito presumido vinculado a receitas tributadas e nao tributadas no mercado interno e de exportacao", ENTRADA, False, False, True, True),
    ("67", "Credito presumido - outras operacoes", ENTRADA, False, False, True, True),
    ("70", "Operacao de aquisicao sem direito a credito", ENTRADA, False, False, False, False),
    ("71", "Operacao de aquisicao com isencao", ENTRADA, False, False, False, False),
    ("72", "Operacao de aquisicao com suspensao", ENTRADA, False, False, False, False),
    ("73", "Operacao de aquisicao a aliquota zero", ENTRADA, False, False, False, False),
    ("74", "Operacao de aquisicao sem incidencia da contribuicao", ENTRADA, False, False, False, False),
    ("75", "Operacao de aquisicao por substituicao tributaria", ENTRADA, False, False, False, False),
    ("98", "Outras operacoes de entrada", ENTRADA, False, False, False, False),
    ("99", "Outras operacoes", AMBOS, False, False, False, False),
)


def carregar(apps, schema_editor):
    Model = apps.get_model("fiscal", "CSTPIS")

    for codigo, descricao, tipo, tributado, aliquota, credito, base in CSTS:
        Model.objects.update_or_create(
            codigo=codigo,
            defaults={
                "descricao": descricao,
                "tipo_operacao": tipo,
                "tributado": tributado,
                "exige_aliquota": aliquota,
                "permite_credito": credito,
                "exige_base_calculo": base,
                "ativo": True,
            },
        )


def remover(apps, schema_editor):
    Model = apps.get_model("fiscal", "CSTPIS")
    Model.objects.filter(
        codigo__in=[item[0] for item in CSTS]
    ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("fiscal", "0011_cst_pis"),
    ]

    operations = [
        migrations.RunPython(
            carregar,
            remover,
        ),
    ]
