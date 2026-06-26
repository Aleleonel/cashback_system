from django.urls import reverse


TEMPLATE_JSON_PLACEHOLDER = 999999


def get_template_json_url_placeholder():
    return reverse(
        'campanhas:detalhe_template_campanha_json',
        kwargs={
            'template_id': TEMPLATE_JSON_PLACEHOLDER
        }
    )


def get_template_json_placeholder():
    return str(TEMPLATE_JSON_PLACEHOLDER)