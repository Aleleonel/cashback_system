from django.db.models import Q, QuerySet

from rh.models import Funcionario


def listar_funcionarios(
    matriz=None,
    ativo=None,
) -> QuerySet:
    queryset = Funcionario.objects.select_related(
        "matriz",
        "cargo",
        "departamento",
    )

    if matriz is not None:
        queryset = queryset.filter(matriz=matriz)

    if ativo is not None:
        queryset = queryset.filter(ativo=ativo)

    return queryset.order_by("nome_completo")


def obter_funcionario_por_id(
    funcionario_id: int,
    matriz=None,
) -> Funcionario:
    queryset = Funcionario.objects.select_related(
        "matriz",
        "cargo",
        "departamento",
    )

    if matriz is not None:
        queryset = queryset.filter(matriz=matriz)

    return queryset.get(pk=funcionario_id)


def buscar_funcionarios(
    termo: str,
    matriz=None,
    ativo=None,
) -> QuerySet:
    queryset = listar_funcionarios(
        matriz=matriz,
        ativo=ativo,
    )

    termo = termo.strip()

    if termo:
        queryset = queryset.filter(
            Q(nome_completo__icontains=termo)
            | Q(cpf__icontains=termo)
            | Q(email__icontains=termo)
        )

    return queryset