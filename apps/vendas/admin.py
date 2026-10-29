from django.contrib import admin
from .models import (
    Cupom, Pedido, ItemPedido, NotificacaoWhatsapp
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


@admin.register(Cupom)
class CupomAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'tipo_desconto', 'valor_desconto', 'valor_minimo', 'usos_atuais', 'limite_uso', 'validade', 'is_ativo']
    list_filter = ['tipo_desconto', 'is_ativo', 'validade']
    search_fields = ['codigo']


@admin.register(NotificacaoWhatsapp)
class NotificacaoWhatsappAdmin(admin.ModelAdmin):
    list_display = ['cliente', 'tipo', 'is_enviada', 'data_envio']
    list_filter = ['tipo', 'is_enviada']
