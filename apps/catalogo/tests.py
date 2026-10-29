from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from .models import Produto, CicloEncomenda, TipoProduto, Tag


class CatalogoModelTests(TestCase):
    def setUp(self):
        self.ciclo = CicloEncomenda.objects.create(
            nome='Ciclo Teste',
            limite_maximo=5,
            quantidade_atual=2,
            is_aberto=True
        )
        self.tipo = TipoProduto.objects.create(nome='Crochê Artesanal')

    def test_status_disponivel_com_estoque(self):
        """Produto com estoque > 0 deve ter status 'disponivel' (Req. F29)."""
        prod = Produto.objects.create(
            nome='Bichinho Estoque',
            preco=Decimal('89.90'),
            estoque=3,
            ciclo_encomenda=self.ciclo,
            tipo_produto=self.tipo
        )
        self.assertEqual(prod.status_disponibilidade, 'disponivel')
        self.assertEqual(prod.status_label, 'Pronta entrega')

    def test_status_encomenda_sem_estoque_com_ciclo_aberto(self):
        """Produto com estoque 0 mas ciclo com vagas deve ser 'encomenda' (Req. F30)."""
        prod = Produto.objects.create(
            nome='Bichinho Encomenda',
            preco=Decimal('120.00'),
            estoque=0,
            ciclo_encomenda=self.ciclo,
            tipo_produto=self.tipo
        )
        self.assertEqual(prod.status_disponibilidade, 'encomenda')
        self.assertEqual(prod.status_label, 'Sob encomenda')

    def test_status_esgotado_ao_atingir_limite(self):
        """Ao fechar o ciclo ou lotar vagas, produto sem estoque fica 'esgotado' (Req. F31)."""
        self.ciclo.quantidade_atual = 5
        self.ciclo.save()
        prod = Produto.objects.create(
            nome='Bichinho Esgotado',
            preco=Decimal('150.00'),
            estoque=0,
            ciclo_encomenda=self.ciclo,
            tipo_produto=self.tipo
        )
        self.assertEqual(prod.status_disponibilidade, 'esgotado')
        self.assertEqual(prod.status_label, 'Esgotado')

    def test_catalogo_abre_detalhe_e_filtra_no_servidor(self):
        produto = Produto.objects.create(
            nome='Bichinho para filtro',
            preco=Decimal('80.00'),
            estoque=1,
            ciclo_encomenda=self.ciclo,
            tipo_produto=self.tipo,
            aprovado=True,
            ativo=True,
        )
        tag = Tag.objects.create(nome='Animais', slug='animais')
        produto.tags.add(tag)

        client = Client()
        response = client.get(reverse('catalogo:home'), {'categoria': 'animais'})
        self.assertContains(response, produto.nome)
        self.assertContains(response, reverse('catalogo:produto_detalhe', args=[produto.id]))

        response = client.get(reverse('catalogo:produto_detalhe', args=[produto.id]))
        self.assertContains(response, produto.nome)

    def test_categorias_marcadas_usam_logica_e(self):
        animais = Tag.objects.create(nome='Animais', slug='animais')
        plantas = Tag.objects.create(nome='Plantas', slug='plantas')
        produto_completo = Produto.objects.create(
            nome='Bichinho com planta', preco=Decimal('90.00'), estoque=1,
            ciclo_encomenda=self.ciclo, tipo_produto=self.tipo, aprovado=True, ativo=True,
        )
        produto_completo.tags.add(animais, plantas)
        produto_parcial = Produto.objects.create(
            nome='Bichinho sem planta', preco=Decimal('70.00'), estoque=1,
            ciclo_encomenda=self.ciclo, tipo_produto=self.tipo, aprovado=True, ativo=True,
        )
        produto_parcial.tags.add(animais)

        response = Client().get(reverse('catalogo:home'), {
            'categoria': ['animais', 'plantas'],
        })
        self.assertContains(response, produto_completo.nome)
        self.assertNotContains(response, produto_parcial.nome)
