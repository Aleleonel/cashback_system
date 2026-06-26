from django.db import transaction

from .models import CampanhaAniversarioEnvio


@transaction.atomic
def registrar_disparos_aniversariantes(
    *,
    matriz,
    clientes,
    canais,
    assunto,
    mensagem,
    template=None,
):
    envios = []

    for cliente in clientes:

        mensagem_personalizada = renderizar_mensagem_template(
            texto=mensagem,
            contexto={
                'nome': cliente.nome,
                'email': cliente.email or '',
                'telefone': cliente.telefone or '',
                'loja': '',
                'saldo': '',
                'dias': '',
            }
        )

        assunto_personalizado = renderizar_mensagem_template(
            texto=assunto,
            contexto={
                'nome': cliente.nome,
                'email': cliente.email or '',
                'telefone': cliente.telefone or '',
                'loja': '',
                'saldo': '',
                'dias': '',
            }
        )

        for canal in canais:
            envios.append(
                CampanhaAniversarioEnvio(
                    matriz=matriz,
                    cliente=cliente,
                    canal=canal,
                    assunto=assunto_personalizado if canal == CampanhaAniversarioEnvio.CANAL_EMAIL else '',
                    mensagem=mensagem_personalizada,
                    template=template,
                    status=CampanhaAniversarioEnvio.STATUS_PENDENTE,
                )
            )

    if envios:
        CampanhaAniversarioEnvio.objects.bulk_create(
            envios,
            batch_size=1000
        )

    return len(envios)


@transaction.atomic
def registrar_reenvio_aniversariante(
    *,
    matriz,
    cliente,
    canais,
    assunto,
    mensagem,
    template=None
):
    envios = []

    contexto_mensagem = {
        'nome': cliente.nome,
        'email': cliente.email or '',
        'telefone': cliente.telefone or '',
        'loja': '',
        'saldo': '',
        'dias': '',
    }

    mensagem_personalizada = renderizar_mensagem_template(
        texto=mensagem,
        contexto=contexto_mensagem
    )

    assunto_personalizado = renderizar_mensagem_template(
        texto=assunto,
        contexto=contexto_mensagem
    )

    for canal in canais:
        envios.append(
            CampanhaAniversarioEnvio(
                matriz=matriz,
                cliente=cliente,
                canal=canal,
                assunto=assunto_personalizado if canal == CampanhaAniversarioEnvio.CANAL_EMAIL else '',
                mensagem=mensagem_personalizada,
                template=template,
                status=CampanhaAniversarioEnvio.STATUS_PENDENTE,
            )
        )

    if envios:
        CampanhaAniversarioEnvio.objects.bulk_create(
            envios,
            batch_size=1000
        )

    return len(envios)

def renderizar_mensagem_template(*, texto, contexto):
    resultado = texto or ''

    for chave, valor in contexto.items():
        resultado = resultado.replace(
            '{' + chave + '}',
            str(valor)
        )

    return resultado


def get_contexto_exemplo_template():
    return {
        'nome': 'Alexandre',
        'saldo': '25,00',
        'loja': 'Pro Corps',
        'dias': '7',
    }