import uuid

from django.db import migrations


def preencher_chaves_idempotencia(apps, schema_editor):
    LancamentoCashback = apps.get_model(
        'cashback',
        'LancamentoCashback',
    )

    lancamentos = list(
        LancamentoCashback.objects.filter(
            chave_idempotencia__isnull=True
        ).only(
            'id',
            'chave_idempotencia',
        )
    )

    for lancamento in lancamentos:
        lancamento.chave_idempotencia = uuid.uuid4()

    if lancamentos:
        LancamentoCashback.objects.bulk_update(
            lancamentos,
            ['chave_idempotencia'],
            batch_size=500,
        )


class Migration(migrations.Migration):

    dependencies = [
        (
            'cashback',
            '0003_lancamentocashback_chave_idempotencia',
        ),
    ]

    operations = [
        migrations.RunPython(
            preencher_chaves_idempotencia,
            reverse_code=migrations.RunPython.noop,
        ),
    ]