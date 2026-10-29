from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib import messages
from django.utils.http import url_has_allowed_host_and_scheme
from django.urls import reverse
from .forms import LoginForm, CadastroClienteForm
from .models import Usuario


def login_view(request):
    """
    Autenticação de usuários.
    Regra de negócio: Se o usuário autenticado for Administrador (ou possuir acesso staff/admin),
    é imediatamente redirecionado ao Django Admin (/admin/).
    """
    next_url = request.GET.get('next') or request.POST.get('next') or ''
    if not url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        next_url = ''

    # Se já estiver autenticado
    if request.user.is_authenticated:
        if request.user.is_staff or request.user.is_superuser or request.user.tipo == Usuario.Tipo.ADMIN:
            return redirect('/admin/')
        if next_url:
            return redirect(next_url)
        return redirect('catalogo:home')

    form_login = LoginForm(request.POST or None)
    form_cadastro = CadastroClienteForm()
    active_tab = 'entrar'

    if request.method == 'POST' and 'btn_entrar' in request.POST:
        if form_login.is_valid():
            user = form_login.cleaned_data['user']
            login(request, user)
            messages.success(request, f'Bem-vinda(o), {user.first_name or user.username}!')

            # Redirecionamento de administrador para o Django Admin
            if user.is_staff or user.is_superuser or user.tipo == Usuario.Tipo.ADMIN:
                return redirect('/admin/')

            if next_url:
                return redirect(next_url)
            return redirect('catalogo:home')
        else:
            active_tab = 'entrar'

    return render(request, 'usuarios/login.html', {
        'form_login': form_login,
        'form_cadastro': form_cadastro,
        'active_tab': active_tab,
        'next': next_url,
    })


def cadastro_view(request):
    """Cadastro de novo cliente com login automático após criação."""
    next_url = request.GET.get('next') or request.POST.get('next') or ''
    if not url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        next_url = ''

    if request.user.is_authenticated:
        return redirect('catalogo:home')

    form_login = LoginForm()
    form_cadastro = CadastroClienteForm(request.POST or None)
    active_tab = 'criar'

    if request.method == 'POST':
        if form_cadastro.is_valid():
            user = form_cadastro.save()
            login(request, user)
            messages.success(request, 'Conta criada com sucesso!')
            if next_url:
                return redirect(next_url)
            return redirect('catalogo:home')
        else:
            active_tab = 'criar'

    return render(request, 'usuarios/login.html', {
        'form_login': form_login,
        'form_cadastro': form_cadastro,
        'active_tab': active_tab,
        'next': next_url,
    })


def logout_view(request):
    """Encerra a sessão do usuário."""
    logout(request)
    messages.info(request, 'Você saiu da sua conta.')
    return redirect('catalogo:home')
