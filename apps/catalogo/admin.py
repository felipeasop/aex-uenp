from django.contrib import admin
from django.utils.html import format_html
from .models import (
    TipoProduto, Tag, Colecao, CicloEncomenda,
    Produto, FotoProduto, SolicitacaoProduto,
    AvisoEstoque, Promocao
)


class FotoProdutoInline(admin.TabularInline):
    model = FotoProduto
    extra = 1
    fields = ['imagem', 'ordem', 'is_principal', 'preview']
    readonly_fields = ['preview']

    def preview(self, instance):
        if instance.imagem:
            return format_html('<img src="{}" style="max-height: 50px; border-radius: 4px;" />', instance.imagem.url)
        return 'Sem imagem'
    preview.short_description = 'Prévia'


@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = ['nome', 'preview_foto', 'preco', 'estoque', 'status_badge', 'aprovado', 'ativo', 'colecao', 'tipo_produto']
    list_filter = ['aprovado', 'ativo', 'tipo_produto', 'colecao', 'tags', 'ciclo_encomenda']
    search_fields = ['nome', 'descricao']
    filter_horizontal = ['tags']
    inlines = [FotoProdutoInline]
    actions = ['aprovar_produtos', 'desativar_produtos']

    def preview_foto(self, obj):
        foto = obj.foto_principal()
        if foto and foto.imagem:
            return format_html('<img src="{}" style="height: 40px; width: 40px; object-fit: cover; border-radius: 4px;" />', foto.imagem.url)
        return '-'
    preview_foto.short_description = 'Foto'

    def status_badge(self, obj):
        status = obj.status_disponibilidade
        cores = {
            'disponivel': '#2e7d32',
            'encomenda': '#c77800',
            'esgotado': '#c62828',
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 12px; font-size: 11px; font-weight: bold;">{}</span>',
            cores.get(status, '#666'),
            obj.status_label
        )
    status_badge.short_description = 'Disponibilidade'

    @admin.action(description='Aprovar produtos selecionados')
    def aprovar_produtos(self, request, queryset):
        queryset.update(aprovado=True)
        self.message_user(request, 'Produtos aprovados com sucesso.')

    @admin.action(description='Desativar produtos selecionados')
    def desativar_produtos(self, request, queryset):
        queryset.update(ativo=False)
        self.message_user(request, 'Produtos desativados com sucesso.')


@admin.register(CicloEncomenda)
class CicloEncomendaAdmin(admin.ModelAdmin):
    list_display = ['nome', 'limite_maximo', 'quantidade_atual', 'is_aberto', 'data_abertura', 'data_fechamento']
    list_filter = ['is_aberto']
    actions = ['fechar_ciclos', 'reabrir_ciclos']

    @admin.action(description='Fechar ciclos selecionados')
    def fechar_ciclos(self, request, queryset):
        for ciclo in queryset:
            ciclo.fechar()
        self.message_user(request, 'Ciclos de encomenda fechados.')

    @admin.action(description='Reabrir ciclos selecionados')
    def reabrir_ciclos(self, request, queryset):
        for ciclo in queryset:
            ciclo.reabrir()
        self.message_user(request, 'Ciclos de encomenda reabertos.')


@admin.register(SolicitacaoProduto)
class SolicitacaoProdutoAdmin(admin.ModelAdmin):
    list_display = ['produto', 'operador', 'status', 'data_solicitacao', 'administrador', 'data_decisao']
    list_filter = ['status', 'data_solicitacao']
    actions = ['aprovar_solicitacoes']

    @admin.action(description='Aprovar solicitações selecionadas')
    def aprovar_solicitacoes(self, request, queryset):
        for sol in queryset:
            sol.aprovar(request.user)
        self.message_user(request, 'Solicitações aprovadas com sucesso.')


@admin.register(TipoProduto)
class TipoProdutoAdmin(admin.ModelAdmin):
    list_display = ['nome', 'descricao']


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['nome', 'slug']
    prepopulated_fields = {'slug': ('nome',)}


@admin.register(Colecao)
class ColecaoAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'is_ativa']
    list_filter = ['is_ativa']


@admin.register(AvisoEstoque)
class AvisoEstoqueAdmin(admin.ModelAdmin):
    list_display = ['cliente', 'produto', 'data_solicitacao', 'notificado']
    list_filter = ['notificado', 'data_solicitacao']


@admin.register(Promocao)
class PromocaoAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'desconto_percentual', 'data_inicio', 'data_fim', 'is_ativa']
    list_filter = ['is_ativa']
