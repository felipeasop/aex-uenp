from django.db import models
from django.contrib.auth.models import AbstractUser


class Usuario(AbstractUser):
    class Tipo(models.TextChoices):
        #Define os três tipos de usuários
        ADMIN = 'ADMIN', 'Administrador'
        OPERADOR = 'OPERADOR', 'Operador'
        CLIENTE = 'CLIENTE', 'Cliente'

    tipo = models.CharField(
        max_length=20,
        choices=Tipo.choices,
        default=Tipo.CLIENTE,
        verbose_name='Tipo de Perfil'
    )
    telefone = models.CharField(
        max_length=25,
        blank=True,
        verbose_name='Telefone / WhatsApp',
        help_text='Utilizado para contato e notificações de pedidos'
    )
    data_nascimento = models.DateField(
        null=True,
        blank=True,
        verbose_name='Data de Nascimento',
        help_text='Utilizado para ações promocionais de aniversário (Req. F12)'
    )

    class Meta:
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'
        ordering = ['username']

    def __str__(self):
        nome = self.get_full_name() or self.username
        return f'{nome} ({self.get_tipo_display()})'

    @property
    def is_administrador(self):
        return self.tipo == self.Tipo.ADMIN or self.is_superuser

    def save(self, *args, **kwargs):
        # Garante que Administradores e Operadores tenham acesso ao painel de administração
        if self.tipo in (self.Tipo.ADMIN, self.Tipo.OPERADOR):
            self.is_staff = True
        super().save(*args, **kwargs)
