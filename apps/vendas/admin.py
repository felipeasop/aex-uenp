from django.contrib import admin
from .models import (
    Cupom, Carrinho, ItemCarrinho, StatusPedido,
    Pedido, ItemPedido, FilaProducao, NotificacaoWhatsapp
)


class ItemPedidoInline(admin.TabularInline):
    model = ItemPedido
    extra = 0
    fields = ['produto', 'quantidade', 'preco_unitario', 'is_encomenda', 'status_producao', 'previsao_entrega']


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ['numero', 'cliente', 'valor_total', 'status', 'status_pagamento', 'metodo_pagamento', 'data_pedido', 'is_entregue']
    list_filter = ['status', 'status_pagamento', 'metodo_pagamento', 'is_entregue', 'data_pedido']
    search_fields = ['numero', 'cliente__username', 'cliente__email', 'cliente__first_name', 'cliente__last_name']
    inlines = [ItemPedidoInline]
    date_hierarchy = 'data_pedido'
    actions = ['marcar_como_pago', 'marcar_como_entregue']

    @admin.action(description='Confirmar pagamento dos pedidos selecionados')
    def marcar_como_pago(self, request, queryset):
        queryset.update(status_pagamento=Pedido.StatusPagamento.APROVADO)
        self.message_user(request, 'Pagamento confirmado para os pedidos selecionados.')

    @admin.action(description='Marcar pedidos selecionados como entregues')
    def marcar_como_entregue(self, request, queryset):
        queryset.update(is_entregue=True)
        self.message_user(request, 'Pedidos marcados como entregues.')


@admin.register(ItemPedido)
class ItemPedidoAdmin(admin.ModelAdmin):
    list_display = ['pedido', 'produto', 'quantidade', 'preco_unitario', 'is_encomenda', 'status_producao']
    list_filter = ['is_encomenda', 'status_producao']
    actions = ['iniciar_producao', 'concluir_producao']

    @admin.action(description='Alterar estado para: Em produção')
    def iniciar_producao(self, request, queryset):
        queryset.update(status_producao=ItemPedido.StatusProducao.EM_PRODUCAO)
        self.message_user(request, 'Itens atualizados para "Em produção".')

    @admin.action(description='Alterar estado para: Pronto para entrega')
    def concluir_producao(self, request, queryset):
        queryset.update(status_producao=ItemPedido.StatusProducao.PRONTO)
        self.message_user(request, 'Itens atualizados para "Pronto para entrega".')


@admin.register(FilaProducao)
class FilaProducaoAdmin(admin.ModelAdmin):
    list_display = ['posicao', 'item_pedido', 'tempo_estimado_dias', 'data_entrada']
    ordering = ['posicao']


@admin.register(Cupom)
class CupomAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'tipo_desconto', 'valor_desconto', 'valor_minimo', 'usos_atuais', 'limite_uso', 'validade', 'is_ativo']
    list_filter = ['tipo_desconto', 'is_ativo', 'validade']
    search_fields = ['codigo']


@admin.register(StatusPedido)
class StatusPedidoAdmin(admin.ModelAdmin):
    list_display = ['nome', 'ordem']


@admin.register(Carrinho)
class CarrinhoAdmin(admin.ModelAdmin):
    list_display = ['id', 'usuario', 'session_key', 'cupom', 'data_atualizacao']


@admin.register(NotificacaoWhatsapp)
class NotificacaoWhatsappAdmin(admin.ModelAdmin):
    list_display = ['cliente', 'tipo', 'is_enviada', 'data_envio']
    list_filter = ['tipo', 'is_enviada']
