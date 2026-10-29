from django.db import models
from django.conf import settings
from django.utils import timezone


class TipoProduto(models.Model):
    """Classificação básica do produto (crochê, pano, misto). Atende Req. F17."""
    nome = models.CharField(max_length=100, unique=True, verbose_name='Nome do Tipo')
    descricao = models.TextField(blank=True, verbose_name='Descrição')

    class Meta:
        verbose_name = 'Tipo de Produto'
        verbose_name_plural = 'Tipos de Produto'
        ordering = ['nome']

    def __str__(self):
        return self.nome


class Tag(models.Model):
    """Tags temáticas para agrupamento e filtragem rápida (Animais, Flores, etc.). Atende Req. F19 e F23."""
    nome = models.CharField(max_length=50, unique=True, verbose_name='Nome da Tag')
    slug = models.SlugField(max_length=60, unique=True, verbose_name='Slug')

    class Meta:
        verbose_name = 'Tag'
        verbose_name_plural = 'Tags'
        ordering = ['nome']

    def __str__(self):
        return self.nome


class Colecao(models.Model):
    """Coleções temáticas personalizadas (ex: Fundo do Mar, Jardim). Atende Req. F18, F20, F21."""
    titulo = models.CharField(max_length=150, verbose_name='Título da Coleção')
    descricao = models.TextField(blank=True, verbose_name='Descrição')
    background = models.ImageField(upload_to='colecoes/', blank=True, null=True, verbose_name='Imagem de Fundo')
    is_ativa = models.BooleanField(default=True, verbose_name='Coleção Ativa')

    class Meta:
        verbose_name = 'Coleção'
        verbose_name_plural = 'Coleções'
        ordering = ['titulo']

    def __str__(self):
        return self.titulo


class CicloEncomenda(models.Model):
    """
    Controla a capacidade de encomendas artesanais do ateliê.
    Atende Req. F26, F27 e F28 (limite máximo de encomendas).
    """
    nome = models.CharField(max_length=100, default='Ciclo Atual', verbose_name='Identificação do Ciclo')
    limite_maximo = models.PositiveIntegerField(default=10, verbose_name='Limite Máximo de Encomendas')
    quantidade_atual = models.PositiveIntegerField(default=0, verbose_name='Quantidade Atual de Encomendas')
    data_abertura = models.DateTimeField(auto_now_add=True, verbose_name='Data de Abertura')
    data_fechamento = models.DateTimeField(null=True, blank=True, verbose_name='Data de Fechamento')
    is_aberto = models.BooleanField(default=True, verbose_name='Ciclo Aberto')

    class Meta:
        verbose_name = 'Ciclo de Encomenda'
        verbose_name_plural = 'Ciclos de Encomenda'
        ordering = ['-data_abertura']

    def __str__(self):
        status = 'Aberto' if self.is_aberto else 'Fechado'
        return f'{self.nome} ({self.quantidade_atual}/{self.limite_maximo} vagas) - {status}'

    def checar_limite(self):
        """Retorna True se ainda houver vaga no ciclo."""
        return self.is_aberto and (self.quantidade_atual < self.limite_maximo)

    def adicionar_encomenda(self, quantidade=1):
        """Registra a entrada de uma nova encomenda no ciclo."""
        self.quantidade_atual += quantidade
        if self.quantidade_atual >= self.limite_maximo:
            # Atingiu o teto do ciclo
            pass
        self.save()

    def fechar(self):
        """Encerra o ciclo de encomendas."""
        self.is_aberto = False
        self.data_fechamento = timezone.now()
        self.save()

    def reabrir(self, novo_limite=None):
        """Reabre o ciclo permitindo novas encomendas."""
        self.is_aberto = True
        if novo_limite:
            self.limite_maximo = novo_limite
        self.data_fechamento = None
        self.save()


class Produto(models.Model):
    """
    Representação central de um produto artesanal (Fofurinho).
    Modelado conforme Astah e Requisitos F17, F26, F27, F28, F29, F30, F31, F32.
    """
    nome = models.CharField(max_length=200, verbose_name='Nome do Fofurinho')
    descricao = models.TextField(verbose_name='Descrição')
    preco = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Preço (R$)')
    tempo_estimado = models.PositiveIntegerField(
        default=10,
        verbose_name='Tempo de Confecção (dias úteis)',
        help_text='Tempo estimado que a artesã leva para produzir a peça (Req. F32)'
    )
    estoque = models.PositiveIntegerField(
        default=0,
        verbose_name='Estoque para Pronta Entrega',
        help_text='Unidades disponíveis para entrega imediata'
    )
    tipo_produto = models.ForeignKey(
        TipoProduto,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='produtos',
        verbose_name='Tipo de Produto'
    )
    colecao = models.ForeignKey(
        Colecao,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='produtos',
        verbose_name='Coleção'
    )
    tags = models.ManyToManyField(
        Tag,
        blank=True,
        related_name='produtos',
        verbose_name='Tags'
    )
    ciclo_encomenda = models.ForeignKey(
        CicloEncomenda,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='produtos',
        verbose_name='Ciclo de Encomenda Vinculado'
    )
    aprovado = models.BooleanField(
        default=True,
        verbose_name='Aprovado pelo Administrador',
        help_text='Produtos cadastrados por operadores necessitam de aprovação (Req. F16)'
    )
    ativo = models.BooleanField(
        default=True,
        verbose_name='Visível na Loja'
    )
    data_criacao = models.DateTimeField(auto_now_add=True, verbose_name='Data de Criação')

    class Meta:
        verbose_name = 'Fofurinho (Produto)'
        verbose_name_plural = 'Fofurinhos (Produtos)'
        ordering = ['-data_criacao']

    def __str__(self):
        return self.nome

    @property
    def status_disponibilidade(self):
        """
        Calcula o status de disponibilidade conforme os requisitos:
        - 'disponivel': se houver unidades em estoque (Req. F29)
        - 'encomenda': sem estoque, mas ciclo de encomendas com vagas abertas (Req. F30)
        - 'esgotado': sem estoque e sem vagas para encomenda (Req. F31)
        """
        if self.estoque > 0:
            return 'disponivel'
        # Verifica se o ciclo vinculado (ou ciclo geral ativo) aceita encomendas
        ciclo = self.ciclo_encomenda or CicloEncomenda.objects.filter(is_aberto=True).first()
        if ciclo and ciclo.checar_limite():
            return 'encomenda'
        return 'esgotado'

    @property
    def status_label(self):
        mapa = {
            'disponivel': 'Pronta entrega',
            'encomenda': 'Sob encomenda',
            'esgotado': 'Esgotado',
        }
        return mapa.get(self.status_disponibilidade, 'Indisponível')

    @property
    def tempo_formatado(self):
        if self.status_disponibilidade == 'disponivel':
            return 'Pronta entrega'
        return f'Até {self.tempo_estimado} dias úteis'

    @property
    def preco_formatado(self):
        return f'{self.preco:.2f}'.replace('.', ',')

    def foto_principal(self):
        """Retorna a foto principal ou a primeira foto cadastrada."""
        foto = self.fotos.filter(is_principal=True).first()
        if not foto:
            foto = self.fotos.first()
        return foto


class FotoProduto(models.Model):
    """Fotos do produto para a galeria do modal/página detalhada."""
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE, related_name='fotos', verbose_name='Produto')
    imagem = models.ImageField(upload_to='produtos/', verbose_name='Arquivo da Imagem')
    ordem = models.PositiveIntegerField(default=0, verbose_name='Ordem de Exibição')
    is_principal = models.BooleanField(default=False, verbose_name='Foto Principal')

    class Meta:
        verbose_name = 'Foto do Produto'
        verbose_name_plural = 'Fotos do Produto'
        ordering = ['ordem', 'id']

    def __str__(self):
        return f'Foto {self.id} de {self.produto.nome}'


class SolicitacaoProduto(models.Model):
    """
    Fluxo de aprovação de produtos adicionados por Operadores.
    Atende Req. F15 e F16 (Aprovação do Administrador).
    """
    class Status(models.TextChoices):
        PENDENTE = 'PENDENTE', 'Pendente'
        APROVADO = 'APROVADO', 'Aprovado'
        RECUSADO = 'RECUSADO', 'Recusado'

    produto = models.OneToOneField(Produto, on_delete=models.CASCADE, related_name='solicitacao', verbose_name='Produto')
    operador = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='solicitacoes_criadas',
        verbose_name='Operador Solicitante'
    )
    administrador = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='solicitacoes_julgadas',
        verbose_name='Administrador Avaliador'
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDENTE, verbose_name='Status')
    motivo_recusa = models.TextField(blank=True, verbose_name='Motivo da Recusa')
    data_solicitacao = models.DateTimeField(auto_now_add=True, verbose_name='Data da Solicitação')
    data_decisao = models.DateTimeField(null=True, blank=True, verbose_name='Data da Decisão')

    class Meta:
        verbose_name = 'Solicitação de Cadastro de Produto'
        verbose_name_plural = 'Solicitações de Cadastro de Produtos'
        ordering = ['-data_solicitacao']

    def __str__(self):
        return f'Solicitação: {self.produto.nome} ({self.get_status_display()})'

    def aprovar(self, admin_user):
        self.status = self.Status.APROVADO
        self.administrador = admin_user
        self.data_decisao = timezone.now()
        self.produto.aprovado = True
        self.produto.save()
        self.save()

    def recusar(self, admin_user, motivo):
        self.status = self.Status.RECUSADO
        self.administrador = admin_user
        self.motivo_recusa = motivo
        self.data_decisao = timezone.now()
        self.produto.aprovado = False
        self.produto.save()
        self.save()


class AvisoEstoque(models.Model):
    """
    Registro de solicitação de aviso quando um produto voltar ao estoque.
    Atende Req. F10.
    """
    cliente = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='avisos_estoque')
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE, related_name='avisos_cadastrados')
    data_solicitacao = models.DateTimeField(auto_now_add=True)
    notificado = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Aviso de Estoque'
        verbose_name_plural = 'Avisos de Estoque'
        unique_together = ['cliente', 'produto']

    def __str__(self):
        return f'{self.cliente} aguarda {self.produto.nome}'


class Favorito(models.Model):
    """Produtos salvos como favoritos pelo cliente. Atende Req. F25."""
    cliente = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='favoritos')
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE, related_name='favoritados')
    data_favoritado = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Produto Favorito'
        verbose_name_plural = 'Produtos Favoritos'
        unique_together = ['cliente', 'produto']

    def __str__(self):
        return f'{self.cliente} favoritou {self.produto.nome}'


class Promocao(models.Model):
    """Campanha promocional. Atende Req. F11."""
    titulo = models.CharField(max_length=150, verbose_name='Título da Promoção')
    descricao = models.TextField(blank=True, verbose_name='Descrição')
    desconto_percentual = models.DecimalField(max_digits=5, decimal_places=2, default=0.0, verbose_name='Desconto (%)')
    data_inicio = models.DateField(verbose_name='Data de Início')
    data_fim = models.DateField(verbose_name='Data de Término')
    is_ativa = models.BooleanField(default=True, verbose_name='Ativa')

    class Meta:
        verbose_name = 'Promoção'
        verbose_name_plural = 'Promoções'
        ordering = ['-data_inicio']

    def __str__(self):
        return f'{self.titulo} ({self.desconto_percentual}%)'

    def esta_vigente(self):
        hoje = timezone.now().date()
        return self.is_ativa and (self.data_inicio <= hoje <= self.data_fim)
