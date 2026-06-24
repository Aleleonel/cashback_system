from django.db.models import Exists, OuterRef
from django.utils import timezone

from clientes.models import Cliente

from .models import CampanhaAniversarioEnvio


def get_aniversariantes_do_mes(*, matriz):

    hoje = timezone.localdate()

    envio_subquery = CampanhaAniversarioEnvio.objects.filter(
        matriz=matriz,
        cliente=OuterRef('pk')
    )

    aniversariantes = Cliente.objects.filter(
        matriz=matriz,
        ativo=True,
        data_nascimento__month=hoje.month
    ).annotate(
        campanha_enviada=Exists(envio_subquery)
    ).only(
        'id',
        'nome',
        'cpf',
        'telefone',
        'email',
        'data_nascimento',
        'aceita_email',
        'aceita_sms',
    ).order_by(
        'data_nascimento__day',
        'nome'
    )

    return aniversariantes