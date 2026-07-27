from django.db import transaction

from .models import ConfiguracaoComercial


@transaction.atomic
def obter_ou_criar_configuracao_comercial(*, matriz):
    configuracao, _ = ConfiguracaoComercial.objects.get_or_create(matriz=matriz)
    return configuracao


@transaction.atomic
def atualizar_configuracao_comercial(*, configuracao, dados):
    campos_permitidos = {
        "atacado_ativo",
        "pedido_minimo_atacado",
        "desconto_atacado_percentual",
        "cashback_ativo",
        "voucher_ativo",
        "promocoes_ativas",
        "brindes_ativos",
        "arredondamento_ativo",
    }

    for campo, valor in dados.items():
        if campo in campos_permitidos:
            setattr(configuracao, campo, valor)

    configuracao.full_clean()
    configuracao.save()
    return configuracao
