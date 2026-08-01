from django.db import transaction

from clientes.models import Cliente
from empresas.models import Loja, Matriz


NOME_CLIENTE_CONSUMIDOR = "CONSUMIDOR"
CPF_CLIENTE_CONSUMIDOR = "CONSUMIDOR"


@transaction.atomic
def obter_ou_criar_cliente_consumidor(*, matriz: Matriz, loja: Loja) -> Cliente:
    if loja.matriz_id != matriz.id:
        raise ValueError("A loja deve pertencer a matriz informada.")

    cliente, criado = Cliente.objects.get_or_create(
        matriz=matriz,
        cpf=CPF_CLIENTE_CONSUMIDOR,
        defaults={
            "loja_cadastro": loja,
            "nome": NOME_CLIENTE_CONSUMIDOR,
            "telefone": None,
            "email": None,
            "aceita_email": False,
            "aceita_sms": False,
            "ativo": True,
        },
    )

    campos_atualizados = []

    if cliente.nome != NOME_CLIENTE_CONSUMIDOR:
        cliente.nome = NOME_CLIENTE_CONSUMIDOR
        campos_atualizados.append("nome")

    if not cliente.ativo:
        cliente.ativo = True
        campos_atualizados.append("ativo")

    if campos_atualizados:
        campos_atualizados.append("atualizado_em")
        cliente.save(update_fields=campos_atualizados)

    return cliente
