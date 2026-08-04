from django.db import migrations


CFOPS = (
    ("1102", "Compra para comercializacao", True, False, False),
    ("1202", "Devolucao de venda de mercadoria adquirida ou recebida de terceiros", True, True, False),
    ("2102", "Compra para comercializacao de outro estado", True, False, False),
    ("2202", "Devolucao de venda de mercadoria adquirida ou recebida de terceiros de outro estado", True, True, False),
    ("3102", "Compra para comercializacao do exterior", True, False, False),
    ("5102", "Venda de mercadoria adquirida ou recebida de terceiros", True, False, False),
    ("5202", "Devolucao de compra para comercializacao", True, True, False),
    ("5405", "Venda de mercadoria adquirida ou recebida de terceiros sujeita a substituicao tributaria", True, False, False),
    ("6102", "Venda de mercadoria adquirida ou recebida de terceiros para outro estado", True, False, False),
    ("6202", "Devolucao de compra para comercializacao de outro estado", True, True, False),
    ("6404", "Venda de mercadoria sujeita a substituicao tributaria para outro estado", True, False, False),
    ("7102", "Venda de mercadoria adquirida ou recebida de terceiros para o exterior", True, False, False),
)


def classificar(codigo):
    primeiro = codigo[0]
    tipo = "entrada" if primeiro in "123" else "saida"

    if primeiro in "15":
        destino = "interna"
    elif primeiro in "26":
        destino = "interestadual"
    else:
        destino = "exterior"

    return tipo, destino


def carregar(apps, schema_editor):
    Model = apps.get_model("fiscal", "CFOP")

    for codigo, descricao, estoque, devolucao, remessa in CFOPS:
        tipo, destino = classificar(codigo)
        Model.objects.update_or_create(
            codigo=codigo,
            defaults={
                "descricao": descricao,
                "tipo_operacao": tipo,
                "destino_operacao": destino,
                "gera_movimento_estoque": estoque,
                "permite_devolucao": devolucao,
                "permite_remessa": remessa,
                "ativo": True,
            },
        )


def remover(apps, schema_editor):
    Model = apps.get_model("fiscal", "CFOP")
    Model.objects.filter(codigo__in=[item[0] for item in CFOPS]).delete()


class Migration(migrations.Migration):
    dependencies = [("fiscal", "0007_cfop")]
    operations = [migrations.RunPython(carregar, remover)]
