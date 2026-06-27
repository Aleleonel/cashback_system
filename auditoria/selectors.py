from .models import RegistroAuditoria


def get_registros_auditoria():

    return RegistroAuditoria.objects.select_related(
        'usuario',
        'matriz',
        'loja',
    ).order_by(
        '-criado_em'
    )