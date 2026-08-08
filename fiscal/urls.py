from django.urls import path

from . import views
from . import views_configuracao_fiscal
from . import views_csosn
from . import views_cfop
from . import views_ncm
from . import views_cst_pis
from . import views_cst_cofins
from . import views_cst_ipi
from . import views_cest
from . import views_beneficio_fiscal
from . import views_regra_fiscal
from . import views_cst_icms


app_name = "fiscal"

urlpatterns = [
    path("", views.inicio, name="inicio"),
    path(
        "configuracao-matriz/",
        views_configuracao_fiscal.configuracao_fiscal_matriz_view,
        name="configuracao_fiscal_matriz",
    ),
    path(
        "origens-mercadoria/",
        views.lista_origens_mercadoria,
        name="lista_origens_mercadoria",
    ),
    path(
        "origens-mercadoria/nova/",
        views.criar_origem_mercadoria_view,
        name="criar_origem_mercadoria",
    ),
    path(
        "origens-mercadoria/<int:origem_id>/editar/",
        views.editar_origem_mercadoria_view,
        name="editar_origem_mercadoria",
    ),
    path("cst-icms/", views_cst_icms.lista_csts_icms, name="lista_csts_icms"),
    path("cst-icms/novo/", views_cst_icms.criar_cst_icms_view, name="criar_cst_icms"),
    path("cst-icms/<int:cst_id>/editar/", views_cst_icms.editar_cst_icms_view, name="editar_cst_icms"),
    path("csosn/", views_csosn.lista_csosns, name="lista_csosns"),
    path("csosn/novo/", views_csosn.criar_csosn_view, name="criar_csosn"),
    path("csosn/<int:csosn_id>/editar/", views_csosn.editar_csosn_view, name="editar_csosn"),

    path("cfop/", views_cfop.lista_cfops, name="lista_cfops"),
    path("cfop/novo/", views_cfop.criar_cfop_view, name="criar_cfop"),
    path("cfop/<int:cfop_id>/editar/", views_cfop.editar_cfop_view, name="editar_cfop"),

    path("ncm/", views_ncm.lista_ncms, name="lista_ncms"),
    path("ncm/novo/", views_ncm.criar_ncm_view, name="criar_ncm"),
    path("ncm/<int:ncm_id>/editar/", views_ncm.editar_ncm_view, name="editar_ncm"),
    path("cst-pis/", views_cst_pis.lista_csts_pis, name="lista_csts_pis"),
    path("cst-pis/novo/", views_cst_pis.criar_cst_pis_view, name="criar_cst_pis"),
    path("cst-pis/<int:cst_pis_id>/editar/", views_cst_pis.editar_cst_pis_view, name="editar_cst_pis"),
    path("cst-cofins/", views_cst_cofins.lista_csts_cofins, name="lista_csts_cofins"),
    path("cst-cofins/novo/", views_cst_cofins.criar_cst_cofins_view, name="criar_cst_cofins"),
    path("cst-cofins/<int:cst_cofins_id>/editar/", views_cst_cofins.editar_cst_cofins_view, name="editar_cst_cofins"),
    path("cst-ipi/", views_cst_ipi.lista_csts_ipi, name="lista_csts_ipi"),
    path("cst-ipi/novo/", views_cst_ipi.criar_cst_ipi_view, name="criar_cst_ipi"),
    path("cst-ipi/<int:cst_ipi_id>/editar/", views_cst_ipi.editar_cst_ipi_view, name="editar_cst_ipi"),
    path("cest/", views_cest.lista_cests, name="lista_cests"),
    path("cest/novo/", views_cest.criar_cest_view, name="criar_cest"),
    path("cest/<int:cest_id>/editar/", views_cest.editar_cest_view, name="editar_cest"),
    path("beneficios-fiscais/", views_beneficio_fiscal.lista_beneficios_fiscais, name="lista_beneficios_fiscais"),
    path("beneficios-fiscais/novo/", views_beneficio_fiscal.criar_beneficio_fiscal_view, name="criar_beneficio_fiscal"),
    path("beneficios-fiscais/<int:beneficio_id>/editar/", views_beneficio_fiscal.editar_beneficio_fiscal_view, name="editar_beneficio_fiscal"),
    path("regras-fiscais/", views_regra_fiscal.lista_regras_fiscais, name="lista_regras_fiscais"),
    path("regras-fiscais/nova/", views_regra_fiscal.criar_regra_fiscal_view, name="criar_regra_fiscal"),
    path("regras-fiscais/<int:regra_id>/editar/", views_regra_fiscal.editar_regra_fiscal_view, name="editar_regra_fiscal"),
]
