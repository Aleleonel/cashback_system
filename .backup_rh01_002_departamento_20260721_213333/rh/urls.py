from django.urls import path

from rh.views.cargo_views import (
    cargo_create,
    cargo_delete,
    cargo_list,
    cargo_update,
)

app_name = "rh"

from .views.inicio import inicio

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
]
