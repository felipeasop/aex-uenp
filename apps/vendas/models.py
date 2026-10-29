from decimal import Decimal
from django.db import models
from django.conf import settings
from django.utils import timezone
from apps.catalogo.models import Produto


class Cupom(models.Model):
    """
    Cupom de desconto promocional.
    Atende Req. F11 e classes Cupom / Desconto do Astah.
    """
    class TipoDesconto(models.TextChoices):
        PERCENTUAL = 'PERCENTUAL', 'Percentual (%)'
        FIXO = 'FIXO', 'Valor Fixo (R$)'

    codigo = models.CharField(max_length=30, unique=True, verbose_name='Código do Cupom')
    validade = models.DateField(verbose_name='Data de Validade')
    limite_uso = models.PositiveIntegerField(default=100, verbose_name='Limite de Usos')
    usos_atuais = models.PositiveIntegerField(default=0, verbose_name='Usos Realizados')
    valor_minimo = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), verbose_name='Valor Mínimo do Pedido (R$)')
    tipo_desconto = models.CharField(max_length=20, choices=TipoDesconto.choices, default=TipoDesconto.PERCENTUAL, verbose_name='Tipo de Desconto')
    valor_desconto = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Valor do Desconto')
    is_ativo = models.BooleanField(default=True, verbose_name='Ativo')

    class Meta:
        verbose_name = 'Cupom de Desconto'
        verbose_name_plural = 'Cupons de Desconto'
        ordering = ['-validade']

    def __str__(self):
        desc = f'{self.valor_desconto}%' if self.tipo_desconto == self.TipoDesconto.PERCENTUAL else f'R$ {self.valor_desconto}'
        return f'{self.codigo} ({desc})'

    def is_valido(self, subtotal=Decimal('0.00')):
        hoje = timezone.now().date()
        if not self.is_ativo:
            return False, 'Este cupom está inativo.'
        if self.validade < hoje:
            return False, 'Este cupom está expirado.'
        if self.usos_atuais >= self.limite_uso:
            return False, 'Limite de usos deste cupom esgotado.'
        if Decimal(str(subtotal)) < self.valor_minimo:
            return False, f'Valor mínimo para uso deste cupom é R$ {self.valor_minimo:.2f}.'
        return True, 'Cupom válido.'

    def calcular_desconto(self, subtotal):
        subtotal = Decimal(str(subtotal))
        valido, _ = self.is_valido(subtotal)
        if not valido:
            return Decimal('0.00')
        if self.tipo_desconto == self.TipoDesconto.PERCENTUAL:
            desconto = subtotal * (self.valor_desconto / Decimal('100.0'))
        else:
            desconto = min(self.valor_desconto, subtotal)
        return round(desconto, 2)

    def registrar_uso(self):
        self.usos_atuais += 1
        self.save()


class Carrinho(models.Model):
    """
    Carrinho de compras da loja.
    Permite uso tanto por visitantes não autenticados (via session_key)
    quanto por clientes autenticados (Req. F04, F05, F08).
    """
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='carrinhos',
        verbose_name='Cliente'
    )
    session_key = models.CharField(max_length=60, blank=True, verbose_name='Chave de Sessão')
    cupom = models.ForeignKey(
        Cupom,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name='Cupom Aplicado'
    )
    data_criacao = models.DateTimeField(auto_now_add=True, verbose_name='Data de Criação')
    data_atualizacao = models.DateTimeField(auto_now=True, verbose_name='Última Atualização')

    class Meta:
        verbose_name = 'Carrinho de Compras'
        verbose_name_plural = 'Carrinhos de Compras'

    def __str__(self):
        dono = self.usuario.username if self.usuario else f'Sessão {self.session_key[:8]}'
        return f'Carrinho de {dono}'

    def calcular_subtotal(self):
        return sum(item.subtotal for item in self.itens.all())

    def calcular_desconto(self):
        if not self.cupom:
            return Decimal('0.00')
        return self.cupom.calcular_desconto(self.calcular_subtotal())

    def calcular_total(self):
        subtotal = self.calcular_subtotal()
        desconto = self.calcular_desconto()
        return max(Decimal('0.00'), subtotal - desconto)

    def total_itens(self):
        return sum(item.quantidade for item in self.itens.all())

    def limpar(self):
        self.itens.all().delete()
        self.cupom = None
        self.save()


class ItemCarrinho(models.Model):
    """Item individual no carrinho de compras."""
    carrinho = models.ForeignKey(Carrinho, on_delete=models.CASCADE, related_name='itens', verbose_name='Carrinho')
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE, verbose_name='Produto')
    quantidade = models.PositiveIntegerField(default=1, verbose_name='Quantidade')

    class Meta:
        verbose_name = 'Item do Carrinho'
        verbose_name_plural = 'Itens do Carrinho'
        unique_together = ['carrinho', 'produto']

    def __str__(self):
        return f'{self.quantidade}x {self.produto.nome}'

    @property
    def subtotal(self):
        return Decimal(str(self.produto.preco)) * self.quantidade


class StatusPedido(models.Model):
    """Status operacional do pedido."""
    nome = models.CharField(max_length=50, unique=True, verbose_name='Nome do Status')
    ordem = models.PositiveIntegerField(default=0, verbose_name='Ordem')

    class Meta:
        verbose_name = 'Status do Pedido'
        verbose_name_plural = 'Status de Pedidos'
        ordering = ['ordem', 'id']

    def __str__(self):
        return self.nome


class Pedido(models.Model):
    """
    Registro formal de uma compra.
    Atende Req. F09 (exige cadastro do cliente), classes Pedido, Pagamento e Entrega do Astah.
    """
    class MetodoPagamento(models.TextChoices):
        PIX = 'PIX', 'Pix'
        CARTAO = 'CARTAO', 'Cartão de Crédito'

    class StatusPagamento(models.TextChoices):
        PENDENTE = 'PENDENTE', 'Aguardando Pagamento'
        APROVADO = 'APROVADO', 'Pagamento Confirmado'
        RECUSADO = 'RECUSADO', 'Pagamento Recusado'
        ESTORNADO = 'ESTORNADO', 'Estornado'

    numero = models.CharField(max_length=32, unique=True, verbose_name='Número do Pedido')
    cliente = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='pedidos',
        verbose_name='Cliente'
    )
    status = models.ForeignKey(
        StatusPedido,
        on_delete=models.PROTECT,
        related_name='pedidos',
        verbose_name='Status do Pedido'
    )
    cupom = models.ForeignKey(
        Cupom,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name='Cupom Utilizado'
    )
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Subtotal (R$)')
    desconto = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), verbose_name='Desconto (R$)')
    frete = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), verbose_name='Frete (R$)')
    valor_total = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Valor Total (R$)')

    # Dados de Pagamento
    metodo_pagamento = models.CharField(max_length=20, choices=MetodoPagamento.choices, default=MetodoPagamento.PIX, verbose_name='Método de Pagamento')
    status_pagamento = models.CharField(max_length=20, choices=StatusPagamento.choices, default=StatusPagamento.PENDENTE, verbose_name='Status do Pagamento')
    codigo_pix = models.TextField(blank=True, verbose_name='Código Pix Copia e Cola / Payload')

    # Dados de Entrega Local (Req. NF01 / Astah LocalEncontro)
    rua = models.CharField(max_length=200, blank=True, verbose_name='Rua / Ponto de Encontro')
    numero_end = models.CharField(max_length=20, blank=True, verbose_name='Número')
    complemento = models.CharField(max_length=100, blank=True, verbose_name='Complemento')
    bairro = models.CharField(max_length=100, blank=True, verbose_name='Bairro')
    cidade = models.CharField(max_length=100, default='Bandeirantes - PR', verbose_name='Cidade')
    observacoes_entrega = models.TextField(blank=True, verbose_name='Observações da Entrega')
    data_prevista_entrega = models.DateField(null=True, blank=True, verbose_name='Data Prevista de Entrega')
    data_entrega = models.DateTimeField(null=True, blank=True, verbose_name='Data da Efetivação da Entrega')
    is_entregue = models.BooleanField(default=False, verbose_name='Entregue')

    data_pedido = models.DateTimeField(auto_now_add=True, verbose_name='Data do Pedido')

    class Meta:
        verbose_name = 'Pedido'
        verbose_name_plural = 'Pedidos'
        ordering = ['-data_pedido']

    def __str__(self):
        return f'Pedido {self.numero} - {self.cliente.first_name or self.cliente.username}'


class ItemPedido(models.Model):
    """
    Item pertencente a um pedido registrado.
    Controla se foi comprado de estoque ou se é encomenda artesanal em produção (Req. F34, F35).
    """
    class StatusProducao(models.TextChoices):
        EM_ESPERA = 'EM_ESPERA', 'Em espera'
        EM_PRODUCAO = 'EM_PRODUCAO', 'Em produção'
        PRONTO = 'PRONTO', 'Pronto para entrega'
        NAO_APLICAVEL = 'NA', 'Pronta Entrega (Estoque)'

    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='itens', verbose_name='Pedido')
    produto = models.ForeignKey(Produto, on_delete=models.PROTECT, related_name='itens_vendidos', verbose_name='Produto')
    quantidade = models.PositiveIntegerField(default=1, verbose_name='Quantidade')
    preco_unitario = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Preço Unitário (R$)')
    is_encomenda = models.BooleanField(default=False, verbose_name='Feito sob Encomenda')
    status_producao = models.CharField(
        max_length=20,
        choices=StatusProducao.choices,
        default=StatusProducao.NAO_APLICAVEL,
        verbose_name='Estado de Produção'
    )
    data_inicio_producao = models.DateTimeField(null=True, blank=True, verbose_name='Início da Produção')
    data_conclusao = models.DateTimeField(null=True, blank=True, verbose_name='Conclusão da Produção')
    previsao_entrega = models.DateField(null=True, blank=True, verbose_name='Previsão de Entrega do Item')

    class Meta:
        verbose_name = 'Item do Pedido'
        verbose_name_plural = 'Itens do Pedido'

    def __str__(self):
        tipo = 'Encomenda' if self.is_encomenda else 'Estoque'
        return f'{self.quantidade}x {self.produto.nome} ({tipo})'

    @property
    def subtotal(self):
        return Decimal(str(self.preco_unitario)) * self.quantidade


class FilaProducao(models.Model):
    """
    Gerenciamento da fila de confecção de encomendas.
    Atende Req. F33 (calcular tempo estimado considerando fila de produção).
    """
    item_pedido = models.OneToOneField(ItemPedido, on_delete=models.CASCADE, related_name='fila', verbose_name='Item da Encomenda')
    posicao = models.PositiveIntegerField(verbose_name='Posição na Fila')
    tempo_estimado_dias = models.PositiveIntegerField(verbose_name='Tempo Estimado (Dias)')
    data_entrada = models.DateTimeField(auto_now_add=True, verbose_name='Entrada na Fila')

    class Meta:
        verbose_name = 'Fila de Produção'
        verbose_name_plural = 'Fila de Produção'
        ordering = ['posicao', 'data_entrada']

    def __str__(self):
        return f'#{self.posicao} - {self.item_pedido.produto.nome} (Pedido {self.item_pedido.pedido.numero})'

    @classmethod
    def tempo_total_fila(cls):
        """Calcula a soma de dias de trabalho atualmente na fila de produção."""
        soma = cls.objects.aggregate(total=models.Sum('tempo_estimado_dias'))['total']
        return soma or 0


class NotificacaoWhatsapp(models.Model):
    """
    Registro para envio de promoções e alertas via WhatsApp.
    Atende Req. F12 e classes NotificacaoWhatsapp do Astah.
    """
    class Tipo(models.TextChoices):
        ANIVERSARIO = 'ANIVERSARIO', 'Promoção de Aniversário'
        PROMOCIONAL = 'PROMOCIONAL', 'Campanha Promocional'
        ESTOQUE = 'ESTOQUE', 'Aviso de Retorno de Estoque'
        PEDIDO = 'PEDIDO', 'Atualização de Pedido'

    cliente = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notificacoes_whatsapp')
    tipo = models.CharField(max_length=20, choices=Tipo.choices, verbose_name='Tipo de Mensagem')
    mensagem = models.TextField(verbose_name='Texto da Mensagem')
    data_envio = models.DateTimeField(null=True, blank=True, verbose_name='Data do Envio')
    is_enviada = models.BooleanField(default=False, verbose_name='Enviada com Sucesso')

    class Meta:
        verbose_name = 'Notificação de WhatsApp'
        verbose_name_plural = 'Notificações de WhatsApp'
        ordering = ['-data_envio']

    def __str__(self):
        return f'Notificação {self.get_tipo_display()} para {self.cliente}'
