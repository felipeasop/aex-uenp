from django import forms
from django.contrib.auth import authenticate
from .models import Usuario

# Formulários de cadastro e login
class LoginForm(forms.Form):
    email = forms.EmailField(
        label='E-mail',
        widget=forms.EmailInput(attrs={'autocomplete': 'email', 'placeholder': 'seu@email.com', 'required': True})
    )
    password = forms.CharField(
        label='Senha',
        widget=forms.PasswordInput(attrs={'autocomplete': 'current-password', 'placeholder': '••••••••', 'required': True})
    )

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        password = cleaned_data.get('password')

        if email and password:
            # Tenta autenticar pelo email (procurando o usuário correspondente)
            user_obj = Usuario.objects.filter(email__iexact=email).first()
            username = user_obj.username if user_obj else email
            user = authenticate(username=username, password=password)
            if not user:
                raise forms.ValidationError('E-mail ou senha incorretos.')
            cleaned_data['user'] = user
        return cleaned_data


class CadastroClienteForm(forms.ModelForm):
    nome = forms.CharField(
        label='Nome Completo',
        max_length=150,
        widget=forms.TextInput(attrs={'autocomplete': 'name', 'placeholder': 'Seu nome completo', 'required': True})
    )
    email = forms.EmailField(
        label='E-mail',
        widget=forms.EmailInput(attrs={'autocomplete': 'email', 'placeholder': 'seu@email.com', 'required': True})
    )
    telefone = forms.CharField(
        label='Telefone / WhatsApp',
        required=False,
        widget=forms.TextInput(attrs={'placeholder': '(00) 00000-0000'})
    )
    password = forms.CharField(
        label='Senha',
        min_length=8,
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password', 'placeholder': 'Mínimo de 8 caracteres', 'required': True})
    )
    confirmar_senha = forms.CharField(
        label='Confirmar Senha',
        min_length=8,
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password', 'placeholder': 'Repita a senha', 'required': True})
    )

    class Meta:
        model = Usuario
        fields = ['email', 'telefone']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if Usuario.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Este e-mail já está cadastrado no sistema.')
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirmar_senha = cleaned_data.get('confirmar_senha')

        if password and confirmar_senha and password != confirmar_senha:
            self.add_error('confirmar_senha', 'As senhas não coincidem.')
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        nome = self.cleaned_data.get('nome', '').strip()
        partes = nome.split(' ', 1)
        user.first_name = partes[0]
        user.last_name = partes[1] if len(partes) > 1 else ''
        # Usamos o email como base do username para unicidade
        user.username = self.cleaned_data['email']
        user.tipo = Usuario.Tipo.CLIENTE
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user
