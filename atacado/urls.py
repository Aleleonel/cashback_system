from django.urls import path
from django.views.generic import RedirectView
from . import views
app_name = "atacado"
urlpatterns = [
    path("", RedirectView.as_view(pattern_name="atacado:orcamentos_lista", permanent=False), name="inicio"),
    path("orcamentos/", views.listar_orcamentos, name="orcamentos_lista"),
    path("orcamentos/novo/", views.novo_orcamento, name="orcamento_novo"),
    path("orcamentos/<int:pk>/acao/", views.acao_orcamento, name="orcamento_acao"),
    path("orcamentos/busca-comercial/", views.f32m5f3d_busca_comercial, name="busca_comercial"),
    path("orcamentos/<int:pk>/exportar/pdf/", views.orcamento_pdf, name="orcamento_pdf"),
    path("orcamentos/<int:pk>/exportar/xlsx/", views.orcamento_xlsx, name="orcamento_xlsx"),
    path("pedidos/", views.listar_pedidos_atacado, name="pedidos_lista"),
    path("pedidos/<int:pk>/consolidar-pdv/", views.consolidar_pedido_atacado_http, name="pedido_consolidar_pdv"),
    path("orcamentos/<int:pk>/cancelar/", views.cancelar_orcamento_atacado_http, name="orcamento_cancelar"),
    path("pedidos/<int:pk>/exportar/pdf/", views.pedido_pdf, name="pedido_pdf"),
    path("pedidos/<int:pk>/exportar/xlsx/", views.pedido_xlsx, name="pedido_xlsx"),
]
