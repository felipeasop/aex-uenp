from decimal import Decimal
from datetime import date, timedelta
from django.test import TestCase, Client
from django.urls import reverse
from apps.usuarios.models import Usuario
from apps.catalogo.models import Produto, CicloEncomenda
from .models import Carrinho, ItemCarrinho, Cupom, StatusPedido, Pedido


class VendasCartAndCheckoutTests(TestCase):
    def setUp(self):
        self.ciclo = CicloEncomenda.objects.create(
            nome='Ciclo Vendas',
            limite_maximo=10,
            quantidade_atual=0,
            is_aberto=True
        )
        self.produto = Produto.objects.create(
            nome='Amigurumi Ursinho',
            preco=Decimal('100.00'),
            estoque=2,
            ciclo_encomenda=self.ciclo,
            aprovado=True,
            ativo=True
        )
        self.cupom = Cupom.objects.create(
            codigo='PROMO10',
            tipo_desconto=Cupom.TipoDesconto.PERCENTUAL,
            valor_desconto=Decimal('10.00'),
            validade=date.today() + timedelta(days=30),
            is_ativo=True
        )
        self.status_inicial = StatusPedido.objects.create(nome='Aguardando Pagamento', ordem=1)
        self.cliente = Usuario.objects.create_user(
            username='comprador@test.com',
            email='comprador@test.com',
            password='password123',
            tipo=Usuario.Tipo.CLIENTE
        )
        self.client = Client()

    def test_carrinho_calculos_e_cupom(self):
        """Testa o cálculo do subtotal, cupom de desconto e valor total."""
        carrinho = Carrinho.objects.create(usuario=self.cliente)
        ItemCarrinho.objects.create(carrinho=carrinho, produto=self.produto, quantidade=2)

        self.assertEqual(carrinho.calcular_subtotal(), Decimal('200.00'))

        # Aplica o cupom de 10%
        carrinho.cupom = self.cupom
        carrinho.save()

        self.assertEqual(carrinho.calcular_desconto(), Decimal('20.00'))
        self.assertEqual(carrinho.calcular_total(), Decimal('180.00'))

    def test_checkout_cria_pedido(self):
        """Testa o fluxo de checkout e geração de pedido com baixa de estoque."""
        self.client.login(username='comprador@test.com', password='password123')
        carrinho = Carrinho.objects.create(usuario=self.cliente)
        ItemCarrinho.objects.create(carrinho=carrinho, produto=self.produto, quantidade=1)

        response = self.client.post(reverse('vendas:checkout'), {
            'rua': 'Av. Central',
            'numero_end': '500',
            'bairro': 'Centro',
            'cidade': 'Bandeirantes - PR',
            'metodo_pagamento': 'PIX',
        })

        self.assertEqual(response.status_code, 302)
        pedido = Pedido.objects.filter(cliente=self.cliente).first()
        self.assertIsNotNone(pedido)
        self.assertEqual(pedido.valor_total, Decimal('100.00'))
        self.assertEqual(pedido.itens.count(), 1)
        
        # O estoque do produto deve ter reduzido de 2 para 1
        self.produto.refresh_from_db()
        self.assertEqual(self.produto.estoque, 1)

    def test_carrinho_e_alteracoes_sao_controlados_pelo_servidor(self):
        """Alterações no carrinho exigem POST e ficam persistidas no Django."""
        url_adicionar = reverse('vendas:adicionar_ao_carrinho', args=[self.produto.id])
        self.assertEqual(self.client.get(url_adicionar).status_code, 405)

        response = self.client.post(url_adicionar)
        self.assertRedirects(response, reverse('vendas:carrinho'))
        carrinho = Carrinho.objects.get(session_key=self.client.session.session_key)
        item = carrinho.itens.get(produto=self.produto)
        self.assertEqual(item.quantidade, 1)

        response = self.client.post(
            reverse('vendas:atualizar_item_carrinho', args=[item.id]),
            {'acao': 'mais'},
        )
        self.assertRedirects(response, reverse('vendas:carrinho'))
        item.refresh_from_db()
        self.assertEqual(item.quantidade, 2)
