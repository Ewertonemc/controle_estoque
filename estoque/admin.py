from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from .models import Produto, Fornecedor, Movimentacao, LogAtividade


@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = (
        'nome', 'categoria', 'quantidade',
        'valor_unitario', 'status_estoque', 'atualizado_em'
    )
    list_filter = ('categoria', 'quantidade_minima')
    search_fields = ('nome', 'nome_normalizado')
    list_editable = ('quantidade', 'valor_unitario')
    readonly_fields = ('valor_total_estoque', 'atualizado_em')
    fieldsets = (
        (None, {
            'fields': ('nome', 'categoria', 'imagem')
        }),
        (_('Estoque'), {
            'fields': (
                'quantidade',
                'quantidade_minima',
                'valor_unitario',
                'valor_total_estoque'
            )
        }),
        (_('Datas'), {
            'fields': ('criado_em', 'atualizado_em'),
            'classes': ('collapse',)
        })
    )

    def status_estoque(self, obj):
        if obj.estoque_baixo:
            return format_html(
                '<div style="color:red; font-weight:bold;">⬇ {}%</div>',
                round((obj.quantidade / obj.quantidade_minima) * 100)
            )
        return format_html(
            '<div style="color:green;">✔</div>'
        )
    status_estoque.short_description = _('Status Estoque')
    status_estoque.admin_order_field = 'quantidade'


@admin.register(Fornecedor)
class FornecedorAdmin(admin.ModelAdmin):
    list_display = (
        'nome_empresa', 'categoria', 'nome_contato',
        'email', 'telefone', 'ativo'
    )
    list_filter = ('categoria', 'ativo')
    search_fields = ('nome_empresa', 'cnpj')
    list_editable = ('ativo',)
    actions = ['ativar_fornecedores', 'desativar_fornecedores']
    fieldsets = (
        (None, {
            'fields': ('nome_empresa', 'categoria', 'ativo')
        }),
        (_('Contato'), {
            'fields': ('nome_contato', 'email', 'telefone')
        }),
        (_('Documentação'), {
            'fields': ('cnpj', 'endereco')
        })
    )

    @admin.action(description=_('Ativar fornecedores selecionados'))
    def ativar_fornecedores(self, request, queryset):
        queryset.update(ativo=True)

    @admin.action(description=_('Desativar fornecedores selecionados'))
    def desativar_fornecedores(self, request, queryset):
        queryset.update(ativo=False)


@admin.register(Movimentacao)
class MovimentacaoAdmin(admin.ModelAdmin):
    list_display = ('data', 'produto', 'tipo', 'quantidade', 'valor_total')
    list_filter = ('tipo', 'data')
    search_fields = ('produto__nome', 'fornecedor__nome_empresa')
    date_hierarchy = 'data'
    readonly_fields = ('valor_total', 'usuario')

    def valor_total(self, obj):
        return f"R$ {obj.valor_total:.2f}"
    valor_total.short_description = _('Valor Total')


@admin.register(LogAtividade)
class LogAtividadeAdmin(admin.ModelAdmin):
    list_display = ('data_hora', 'usuario', 'acao',
                    'modelo_afetado', 'objeto_id')
    list_filter = ('acao', 'modelo_afetado')
    search_fields = ('usuario__username', 'descricao')
    readonly_fields = ('data_hora', 'usuario', 'detalhes')
    date_hierarchy = 'data_hora'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
