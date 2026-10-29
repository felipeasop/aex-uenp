from django.urls import path
from . import views

app_name = 'catalogo'

urlpatterns = [
    path('', views.home_view, name='home'),
    path('produto/<int:produto_id>/', views.produto_detalhe_view, name='produto_detalhe'),
    path('api/produto/<int:produto_id>/', views.produto_detalhe_api, name='produto_detalhe_api'),
    path('aviso-estoque/<int:produto_id>/', views.solicitar_aviso_estoque, name='solicitar_aviso_estoque'),
]
