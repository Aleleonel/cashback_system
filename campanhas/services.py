from django.db import transaction

from .models import CampanhaAniversarioEnvio


@transaction.atomic
def registrar_disparos_aniversariantes(
    *,
    matriz,
    clientes,
    canais,
    assunto,
    mensagem
):
    envios = []

    for cliente in clientes:

        mensagem_personalizada = mensagem.format(
            nome=cliente.nome
        )

        for canal in canais:
            envios.append(
                CampanhaAniversarioEnvio(
                    matriz=matriz,
                    cliente=cliente,
                    canal=canal,
                    assunto=assunto if canal == CampanhaAniversarioEnvio.CANAL_EMAIL else '',
                    mensagem=mensagem_personalizada,
                    status=CampanhaAniversarioEnvio.STATUS_PENDENTE,
                )
            )

    if envios:
        CampanhaAniversarioEnvio.objects.bulk_create(
            envios,
            batch_size=1000
        )

    return len(envios)