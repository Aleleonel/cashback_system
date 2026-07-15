from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404


def obter_por_selector_ou_404(
    selector,
    **kwargs,
):
    try:
        return selector(**kwargs)
    except ObjectDoesNotExist as erro:
        raise Http404(
            'Registro não encontrado.'
        ) from erro


def aplicar_erros_validacao_no_form(
    *,
    form,
    erro,
):
    message_dict = getattr(
        erro,
        'message_dict',
        None
    )

    if message_dict:
        for campo, mensagens in message_dict.items():
            campo_form = (
                campo
                if campo in form.fields
                else None
            )

            for mensagem in mensagens:
                form.add_error(
                    campo_form,
                    mensagem
                )

        return

    mensagens = getattr(
        erro,
        'messages',
        [str(erro)]
    )

    for mensagem in mensagens:
        form.add_error(
            None,
            mensagem
        )
