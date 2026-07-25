from django.db.models import QuerySet

from rh.models import Cargo


def listar_cargos(
    matriz=None,
    ativo=True,
) -> QuerySet:
    """
    Retorna os cargos da matriz.
    """

    queryset = Cargo.objects.select_related(
        "matriz"
    )

    if matriz is not None:
        queryset = queryset.filter(
            matriz=matriz
        )

    if ativo is not None:
        queryset = queryset.filter(
            ativo=ativo
        )

    return queryset.order_by("nome")


def obter_cargo_por_id(
    cargo_id: int,
) -> Cargo:
    """
    Retorna um cargo pelo ID.
    """

    return (
        Cargo.objects.select_related("matriz")
        .get(pk=cargo_id)
    )


def buscar_cargos(
    termo: str,
    matriz=None,
    ativo=True,
) -> QuerySet:
    """
    Pesquisa cargos pelo nome.
    """

    queryset = listar_cargos(
        matriz=matriz,
        ativo=ativo,
    )

    if termo:
        queryset = queryset.filter(
            nome__icontains=termo.strip()
        )

    return queryset