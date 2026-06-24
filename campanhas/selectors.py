from django.db.models import Exists, OuterRef, Subquery
from django.utils import timezone

from clientes.models import Cliente

from .models import CampanhaAniversarioEnvio


def get_aniversariantes_do_mes(*, matriz):

    hoje = timezone.localdate()

    ultimo_envio = CampanhaAniversarioEnvio.objects.filter(
        matriz=matriz,
        cliente=OuterRef('pk')
    ).order_by(
        '-criado_em'
    )

    aniversariantes = Cliente.objects.filter(
        matriz=matriz,
        ativo=True,
        data_nascimento__month=hoje.month
    ).annotate(
        campanha_enviada=Exists(ultimo_envio),
        ultimo_envio_data=Subquery(
            ultimo_envio.values('criado_em')[:1]
        ),
        ultimo_envio_canal=Subquery(
            ultimo_envio.values('canal')[:1]
        ),
        ultimo_envio_status=Subquery(
            ultimo_envio.values('status')[:1]
        ),
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