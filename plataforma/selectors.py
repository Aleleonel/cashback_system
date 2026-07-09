from django.db.models import Count, Q

from accounts.models import Usuario
from campanhas.models import CampanhaAniversarioEnvio, TemplateCampanha
from cashback.models import LancamentoCashback, UsoCashback
from clientes.models import Cliente
from core.choices import StatusOperacional
from empresas.models import Loja, Matriz


def get_resumo_painel_master():

    return {
        'total_matrizes': Matriz.objects.count(),
        'matrizes_ativas': Matriz.objects.filter(
            status=StatusOperacional.ATIVA
        ).count(),
        'total_lojas': Loja.objects.count(),
        'lojas_ativas': Loja.objects.filter(            
            status=StatusOperacional.ATIVA
        ).count(),
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

    if status:
        matrizes = matrizes.filter(
            status=status
        )

    return matrizes


def get_lojas_plataforma(*, busca='', status='', matriz_id=''):

    lojas = Loja.objects.select_related(
        'matriz'
    ).order_by(
        'matriz__nome',
        'nome'
    )

    if busca:
        lojas = lojas.filter(
            Q(nome__icontains=busca) |
            Q(cnpj__icontains=busca) |
            Q(telefone__icontains=busca) |
            Q(matriz__nome__icontains=busca)
        )

    if status:
        lojas = lojas.filter(
            status=status
        )

    if matriz_id:
        lojas = lojas.filter(
            matriz_id=matriz_id
        )

    return lojas