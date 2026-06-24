from django.utils import timezone

from clientes.models import Cliente


def get_aniversariantes_do_mes(*, matriz):
    hoje = timezone.localdate()

    return Cliente.objects.filter(
        matriz=matriz,
        ativo=True,
        data_nascimento__month=hoje.month
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