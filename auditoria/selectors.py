from .models import RegistroAuditoria


def get_registros_auditoria(
    *,
    acao='',
    busca='',
    data_inicio='',
    data_fim=''
):

    registros = RegistroAuditoria.objects.select_related(
        'usuario',
        'matriz',
        'loja',
    ).order_by(
        '-criado_em'
    )

    if acao:
        registros = registros.filter(
            acao=acao
        )

    if busca:
        registros = registros.filter(
            usuario__username__icontains=busca
        ) | registros.filter(
            matriz__nome__icontains=busca
        ) | registros.filter(
            loja__nome__icontains=busca
        ) | registros.filter(
            recurso__icontains=busca
        ) | registros.filter(
            descricao__icontains=busca
        ) | registros.filter(
            ip__icontains=busca
        )

    if data_inicio:
        registros = registros.filter(
            criado_em__date__gte=data_inicio
        )

    if data_fim:
        registros = registros.filter(
            criado_em__date__lte=data_fim
        )

    return registros