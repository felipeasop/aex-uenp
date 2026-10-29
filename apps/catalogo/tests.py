from decimal import Decimal
from django.test import TestCase
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
