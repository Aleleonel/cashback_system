from .models import ConfiguracaoComercial


def get_configuracao_comercial(*, matriz):
    return ConfiguracaoComercial.objects.filter(matriz=matriz).first()
