from django.urls import path
from . import views

app_name = 'financeiro'
urlpatterns = [
    path("", views.painel, name="painel"),
    path("titulos/", views.titulos, name="titulos"),
    path("titulos/exportar.csv", views.titulos_exportar_csv, name="titulos_exportar_csv"),
    path("titulos/importar.csv", views.titulos_importar_csv, name="titulos_importar_csv"),
    path("titulos/<uuid:titulo_uuid>/", views.titulo_detalhe, name="titulo_detalhe"),
    path("titulos/<uuid:titulo_uuid>/cancelar/", views.titulo_cancelar, name="titulo_cancelar"),
    path("titulos/<uuid:titulo_uuid>/parcelas/<int:parcela_id>/baixa/", views.parcela_baixa_nova, name="parcela_baixa_nova"),
    path("titulos/<uuid:titulo_uuid>/parcelas/<int:parcela_id>/baixas/<int:baixa_id>/estornar/", views.baixa_estornar, name="baixa_estornar"),
    path("planos-conta/", views.planos_conta, name="planos_conta"),
    path("planos-conta/novo/", views.plano_conta_novo, name="plano_conta_novo"),
    path("planos-conta/<uuid:plano_uuid>/editar/", views.plano_conta_editar, name="plano_conta_editar"),
    path("centros-custo/", views.centros_custo, name="centros_custo"),
    path("centros-custo/novo/", views.centro_custo_novo, name="centro_custo_novo"),
    path("centros-custo/<uuid:centro_uuid>/editar/", views.centro_custo_editar, name="centro_custo_editar"),
    path("instituicoes-bancarias/", views.instituicoes_bancarias, name="instituicoes_bancarias"),
    path("instituicoes-bancarias/nova/", views.instituicao_bancaria_nova, name="instituicao_bancaria_nova"),
    path("instituicoes-bancarias/<uuid:instituicao_uuid>/editar/", views.instituicao_bancaria_editar, name="instituicao_bancaria_editar"),
    path("contas-financeiras/", views.contas_financeiras, name="contas_financeiras"),
    path("contas-financeiras/nova/", views.conta_financeira_nova, name="conta_financeira_nova"),
    path("contas-financeiras/<uuid:conta_uuid>/editar/", views.conta_financeira_editar, name="conta_financeira_editar"),
    path("lancamentos/novo/", views.lancamento_manual, name="lancamento_manual"),
]
