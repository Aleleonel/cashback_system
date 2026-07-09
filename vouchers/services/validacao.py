def validar_voucher(*, voucher):

    if not voucher.esta_ativo:
        return False, 'Voucher inativo.'

    if voucher.ainda_nao_iniciado:
        return False, 'Voucher ainda não está vigente.'

    if voucher.esta_expirado:
        return False, 'Voucher expirado.'

    if voucher.esta_esgotado:
        return False, 'Voucher sem utilizações disponíveis.'

    return True, ''