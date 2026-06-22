from .models import Cliente


def get_cliente_por_cpf(*, matriz, cpf):
    return Cliente.objects.filter(
        matriz=matriz,
        cpf=cpf
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

def get_cliente_por_cpf(matriz, cpf):
    return Cliente.objects.filter(
        matriz=matriz,
        cpf=cpf,
        ativo=True
    ).first()