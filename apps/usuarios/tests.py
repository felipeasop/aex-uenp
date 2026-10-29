from django.test import TestCase, Client
from django.urls import reverse
from .models import Usuario


class UsuarioAuthTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin_user = Usuario.objects.create_user(
            username='admin_test',
            email='admin@test.com',
            password='password123',
            tipo=Usuario.Tipo.ADMIN,
            is_staff=True,
            is_superuser=True
        )
        self.cliente_user = Usuario.objects.create_user(
            username='cliente@test.com',
            email='cliente@test.com',
            password='password123',
            tipo=Usuario.Tipo.CLIENTE
        )

    def test_admin_login_redirects_to_admin(self):
        """Verifica se o login do administrador é redirecionado para /admin/ conforme o requisito."""
        response = self.client.post(reverse('usuarios:login'), {
            'btn_entrar': '1',
            'email': 'admin@test.com',
            'password': 'password123',
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/admin/')

    def test_cliente_login_redirects_to_home_or_next(self):
        """Verifica se o login do cliente normal não vai para /admin/ e sim para a loja."""
        response = self.client.post(reverse('usuarios:login'), {
            'btn_entrar': '1',
            'email': 'cliente@test.com',
            'password': 'password123',
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('catalogo:home'))

    def test_cliente_cadastro(self):
        """Testa o cadastro de novo cliente."""
        response = self.client.post(reverse('usuarios:cadastro'), {
            'nome': 'Ana Clara',
            'email': 'anaclara@exemplo.com',
            'telefone': '(43) 98888-7777',
            'password': 'novasenha123',
            'confirmar_senha': 'novasenha123',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Usuario.objects.filter(email='anaclara@exemplo.com').exists())
