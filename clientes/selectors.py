from django.db import models

from .models import Cliente
from .utils import limpar_numero, normalizar_texto


def get_cliente_por_cpf(*, matriz, cpf):
    cpf_normalizado = limpar_numero(cpf)

    return Cliente.objects.filter(
        matriz=matriz,
        cpf_normalizado=cpf_normalizado,
        ativo=True
    ).select_related(
        'matriz',
        'loja_cadastro'
    ).first()


def get_clientes_da_matriz(*, matriz):
    return Cliente.objects.filter(
        matriz=matriz,
        ativo=True
    ).select_related(
        'matriz',
        'loja_cadastro'
    ).order_by('nome')


def aplicar_busca_clientes(queryset, busca):
    busca = (busca or '').strip()

    if not busca:
        return queryset

    busca_numerica = limpar_numero(busca)
    busca_texto = normalizar_texto(busca)

    filtros = (
        models.Q(nome__icontains=busca) |
        models.Q(email__icontains=busca) |
        models.Q(nome_normalizado__icontains=busca_texto) |
        models.Q(email_normalizado__icontains=busca_texto)
    )

    if busca_numerica:
        filtros = filtros | (
            models.Q(cpf__icontains=busca) |
            models.Q(telefone__icontains=busca) |
            models.Q(cpf_normalizado__icontains=busca_numerica) |
            models.Q(telefone_normalizado__icontains=busca_numerica)
        )

    return queryset.filter(filtros)