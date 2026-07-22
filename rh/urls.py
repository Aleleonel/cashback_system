from django.urls import path

from rh.views.cargo_views import (
    cargo_create,
    cargo_delete,
    cargo_list,
    cargo_update,
)
from rh.views.departamento_views import (
    departamento_create,
    departamento_delete,
    departamento_list,
    departamento_update,
)
from rh.views.inicio import inicio


app_name = "rh"


urlpatterns = [
    path("", inicio, name="inicio"),

    # Cargo
    path(
        "cargos/",
        cargo_list,
        name="cargo_list",
    ),
    path(
        "cargos/novo/",
        cargo_create,
        name="cargo_create",
    ),
    path(
        "cargos/<int:pk>/editar/",
        cargo_update,
        name="cargo_update",
    ),
    path(
        "cargos/<int:pk>/excluir/",
        cargo_delete,
        name="cargo_delete",
    ),

    # Departamento
    path(
        "departamentos/",
        departamento_list,
        name="departamento_list",
    ),
    path(
        "departamentos/novo/",
        departamento_create,
        name="departamento_create",
    ),
    path(
        "departamentos/<int:pk>/editar/",
        departamento_update,
        name="departamento_update",
    ),
    path(
        "departamentos/<int:pk>/inativar/",
        departamento_delete,
        name="departamento_delete",
    ),
]