from accounts.models import Usuario
from campanhas.models import CampanhaAniversarioEnvio, TemplateCampanha
from cashback.models import LancamentoCashback, UsoCashback
from clientes.models import Cliente
from empresas.models import Loja, Matriz


def get_resumo_painel_master():

    return {
        'total_matrizes': Matriz.objects.count(),
        'matrizes_ativas': Matriz.objects.filter(ativa=True).count(),
        'total_lojas': Loja.objects.count(),
        'lojas_ativas': Loja.objects.filter(ativa=True).count(),
        'total_usuarios': Usuario.objects.count(),
        'usuarios_ativos': Usuario.objects.filter(ativo=True).count(),
        'total_clientes': Cliente.objects.count(),
        'total_lancamentos_cashback': LancamentoCashback.objects.count(),
        'total_usos_cashback': UsoCashback.objects.count(),
        'total_envios_campanhas': CampanhaAniversarioEnvio.objects.count(),
        'total_templates_campanhas': TemplateCampanha.objects.count(),
    }