from django.urls import path
from . import views

app_name = 'vendas'

urlpatterns = [
    path('carrinho/', views.carrinho_view, name='carrinho'),
    path('adicionar/<int:produto_id>/', views.adicionar_ao_carrinho, name='adicionar_ao_carrinho'),
    path('item/<int:item_id>/atualizar/', views.atualizar_item_carrinho, name='atualizar_item_carrinho'),
    path('cupom/aplicar/', views.aplicar_cupom, name='aplicar_cupom'),
    path('cupom/remover/', views.remover_cupom, name='remover_cupom'),
    path('checkout/', views.checkout_view, name='checkout'),
    path('confirmacao/<int:pedido_id>/', views.confirmacao_view, name='confirmacao'),
]
