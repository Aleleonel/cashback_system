from django.urls import path
from . import views

app_name = 'financeiro'
urlpatterns = [
    path("", views.painel, name="painel"),
    path("titulos/", views.titulos, name="titulos"),
    path("titulos/<uuid:titulo_uuid>/", views.titulo_detalhe, name="titulo_detalhe"),
    path("titulos/<uuid:titulo_uuid>/parcelas/<int:parcela_id>/baixa/", views.parcela_baixa_nova, name="parcela_baixa_nova"),
    path("planos-conta/", views.planos_conta, name="planos_conta"),
    path("planos-conta/novo/", views.plano_conta_novo, name="plano_conta_novo"),
    path("planos-conta/<uuid:plano_uuid>/editar/", views.plano_conta_editar, name="plano_conta_editar"),
    path("centros-custo/", views.centros_custo, name="centros_custo"),
    path("centros-custo/novo/", views.centro_custo_novo, name="centro_custo_novo"),
    path("instituicoes-bancarias/", views.instituicoes_bancarias, name="instituicoes_bancarias"),
    path("instituicoes-bancarias/nova/", views.instituicao_bancaria_nova, name="instituicao_bancaria_nova"),
    path("contas-financeiras/", views.contas_financeiras, name="contas_financeiras"),
    path("contas-financeiras/nova/", views.conta_financeira_nova, name="conta_financeira_nova"),
    path("lancamentos/novo/", views.lancamento_manual, name="lancamento_manual"),
]
