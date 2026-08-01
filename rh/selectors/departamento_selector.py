from django.db.models import QuerySet

from rh.models import Departamento


def listar_departamentos(
    matriz=None,
    ativo=True,
) -> QuerySet:
    """
    Retorna os departamentos da matriz.
    """

    queryset = Departamento.objects.select_related("matriz")

    if matriz is not None:
        queryset = queryset.filter(matriz=matriz)

    if ativo is not None:
        queryset = queryset.filter(ativo=ativo)

    return queryset.order_by("nome")


def obter_departamento_por_id(
    departamento_id: int,
    matriz=None,
) -> Departamento:
    """
    Retorna um departamento pelo ID.
    """

    queryset = Departamento.objects.select_related("matriz")

    if matriz is not None:
        queryset = queryset.filter(matriz=matriz)

    return queryset.get(pk=departamento_id)


def buscar_departamentos(
    termo: str,
    matriz=None,
    ativo=True,
) -> QuerySet:
    """
    Pesquisa departamentos pelo nome.
    """

    queryset = listar_departamentos(
        matriz=matriz,
        ativo=ativo,
    )

    if termo:
        queryset = queryset.filter(
            nome__icontains=termo.strip()
        )

    return queryset