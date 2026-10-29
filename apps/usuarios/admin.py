from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'tipo', 'telefone', 'is_staff', 'is_active']
    list_filter = ['tipo', 'is_staff', 'is_superuser', 'is_active']
    search_fields = ['username', 'email', 'first_name', 'last_name', 'telefone']

    fieldsets = UserAdmin.fieldsets + (
        ('Informações Específicas do Perfil', {
            'fields': ('tipo', 'telefone', 'data_nascimento')
        }),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Informações Específicas do Perfil', {
            'fields': ('tipo', 'telefone', 'data_nascimento')
        }),
    )
