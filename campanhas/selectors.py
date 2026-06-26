from django.utils import timezone

from clientes.models import Cliente

from .models import (
    CampanhaAniversarioEnvio,
    ConfiguracaoCampanhaAniversario,
    TemplateCampanha,
)

from django.db.models import Count, Exists, OuterRef, Subquery


def get_aniversariantes_do_mes(*, matriz):

    hoje = timezone.localdate()

    ultimo_envio = CampanhaAniversarioEnvio.objects.filter(
        matriz=matriz,
        cliente=OuterRef('pk')
    ).order_by(
        '-criado_em'
    )

    total_envios_subquery = (
        CampanhaAniversarioEnvio.objects
        .filter(
            matriz=matriz,
            cliente=OuterRef('pk')
        )
        .values('cliente')
        .annotate(total=Count('id'))
        .values('total')[:1]
    )

    aniversariantes = Cliente.objects.filter(
        matriz=matriz,
        ativo=True,
        data_nascimento__month=hoje.month
    ).annotate(
        campanha_enviada=Exists(ultimo_envio),
        ultimo_envio_data=Subquery(
            ultimo_envio.values('criado_em')[:1]
        ),
        ultimo_envio_canal=Subquery(
            ultimo_envio.values('canal')[:1]
        ),
        ultimo_envio_status=Subquery(
            ultimo_envio.values('status')[:1]
        ),
        total_envios=Subquery(total_envios_subquery),
    ).only(
        'id',
        'nome',
        'cpf',
        'telefone',
        'email',
        'data_nascimento',
        'aceita_email',
        'aceita_sms',
    ).order_by(
        'data_nascimento__day',
        'nome'
    )

    return aniversariantes


def get_historico_envios_aniversario(*, matriz):

    return CampanhaAniversarioEnvio.objects.filter(
        matriz=matriz
    ).select_related(
        'cliente'
    ).only(
        'id',
        'cliente__nome',
        'cliente__cpf',
        'canal',
        'status',
        'assunto',
        'mensagem',
        'criado_em',
        'enviado_em',
    ).order_by(
        '-criado_em'
    )

def get_fila_envios_aniversario(*, matriz):

    return CampanhaAniversarioEnvio.objects.filter(
        matriz=matriz,
        status__in=[
            CampanhaAniversarioEnvio.STATUS_PENDENTE,
            CampanhaAniversarioEnvio.STATUS_PROCESSANDO,
            CampanhaAniversarioEnvio.STATUS_ERRO,
        ]
    ).select_related(
        'cliente'
    ).only(
        'id',
        'cliente__nome',
        'cliente__cpf',
        'canal',
        'status',
        'assunto',
        'erro',
        'criado_em',
        'enviado_em',
    ).order_by(
        'status',
        'criado_em'
    )

def get_configuracao_campanha_aniversario(*, matriz):

    configuracao, criada = ConfiguracaoCampanhaAniversario.objects.get_or_create(
        matriz=matriz
    )

    return configuracao

def get_templates_campanhas(*, matriz):

    return TemplateCampanha.objects.filter(
        matriz=matriz
    ).order_by(
        'nome'
    )