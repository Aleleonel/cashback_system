from accounts.models import Usuario
from campanhas.models import CampanhaAniversarioEnvio, TemplateCampanha
from cashback.models import LancamentoCashback, UsoCashback
from clientes.models import Cliente
from empresas.models import Loja, Matriz
from django.db.models import Count, Q



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


def get_matrizes_plataforma(*, busca='', status=''):

    matrizes = Matriz.objects.annotate(
        total_lojas=Count('lojas', distinct=True),
        total_usuarios=Count('usuarios', distinct=True),
    ).order_by(
        'nome'
    )

    if busca:
        matrizes = matrizes.filter(
            Q(nome__icontains=busca) |
            Q(cnpj__icontains=busca)
        )

    if status == 'ativas':
        matrizes = matrizes.filter(
            ativa=True
        )

    if status == 'inativas':
        matrizes = matrizes.filter(
            ativa=False
        )

    return matrizes