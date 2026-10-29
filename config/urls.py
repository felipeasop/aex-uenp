"""
URL configuration for Lua e Flor - Loja de Crochê.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from apps.vendas.views import carrinho_view
from apps.usuarios.views import login_view, logout_view

# Customização do Django Admin
admin.site.site_header = 'Lua e Flor · Ateliê de Crochê'
admin.site.site_title = 'Administração Lua e Flor'
admin.site.index_title = 'Painel de Controle da Loja'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.catalogo.urls', namespace='catalogo')),
    path('vendas/', include('apps.vendas.urls', namespace='vendas')),
    path('conta/', include('apps.usuarios.urls', namespace='usuarios')),

    # Atalhos convenientes para compatibilidade direta com os links do template
    path('carrinho/', carrinho_view, name='atalho_carrinho'),
    path('entrar/', login_view, name='atalho_login'),
    path('login/', login_view, name='atalho_login_alt'),
    path('sair/', logout_view, name='atalho_logout'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
