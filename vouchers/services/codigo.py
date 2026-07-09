import secrets

from django.utils import timezone

from vouchers.models import Voucher


CARACTERES_CODIGO = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'


def gerar_codigo_voucher():

    ano = timezone.localdate().strftime('%y')

    while True:

        codigo = (
            f'VCH-{ano}-'
            f'{"".join(secrets.choice(CARACTERES_CODIGO) for _ in range(6))}'
        )

        if not Voucher.objects.filter(codigo=codigo).exists():
            return codigo