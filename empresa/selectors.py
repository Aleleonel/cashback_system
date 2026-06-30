from cashback.models import LancamentoCashback
from clientes.models import Cliente
from empresas.models import Loja
from accounts.models import Usuario
from campanhas.models import CampanhaAniversarioEnvio


def get_resumo_minha_empresa(*, matriz):

    return {
        'total_lojas': Loja.objects.filter(
            matriz=matriz
        ).count(),

        'lojas_ativas': Loja.objects.filter(
            matriz=matriz,
            status='ativa'
        ).count(),

        'usuarios_ativos': Usuario.objects.filter(
            matriz=matriz,
            ativo=True
        ).count(),

        'total_clientes': Cliente.objects.filter(
            matriz=matriz,
            ativo=True
        ).count(),

        'total_lancamentos_cashback': LancamentoCashback.objects.filter(
            matriz=matriz
        ).count(),

        'total_envios_campanhas': CampanhaAniversarioEnvio.objects.filter(
            matriz=matriz
        ).count(),
    }