from .models import Cliente


def limpar_numero(valor):
    return ''.join(filter(str.isdigit, valor or ''))


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