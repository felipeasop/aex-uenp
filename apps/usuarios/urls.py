from django.urls import path
from . import views

app_name = 'usuarios'

urlpatterns = [
    path('entrar/', views.login_view, name='login'),
    path('cadastro/', views.cadastro_view, name='cadastro'),
    path('sair/', views.logout_view, name='logout'),
]
