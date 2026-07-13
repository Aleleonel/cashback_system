from django.core.exceptions import ValidationError

from produtos.models import UnidadeMedida


def normalizar_sigla_unidade(sigla):
    return (sigla or '').strip().upper()


def normalizar_descricao_unidade(descricao):
    return (descricao or '').strip()


def validar_sigla_unidade(
    *,
    matriz,
    sigla,
    unidade_excluida=None,
):
    sigla = normalizar_sigla_unidade(sigla)

    if not sigla:
        raise ValidationError({
            'sigla': 'Informe a sigla da unidade de medida.'
        })

    unidades = UnidadeMedida.objects.filter(
        matriz=matriz,
        sigla__iexact=sigla,
    )

    if unidade_excluida is not None:
        unidades = unidades.exclude(
            id=unidade_excluida.id
        )

    if unidades.exists():
        raise ValidationError({
            'sigla': (
                'Já existe uma unidade de medida com esta sigla.'
            )
        })

    return sigla


def validar_descricao_unidade(descricao):
    descricao = normalizar_descricao_unidade(descricao)

    if not descricao:
        raise ValidationError({
            'descricao': (
                'Informe a descrição da unidade de medida.'
            )
        })

    return descricao
