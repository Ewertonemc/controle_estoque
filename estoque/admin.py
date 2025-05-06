from django.contrib import admin
from .models import Fornecedor, Produto


@admin.register(Fornecedor)
class FornecedorAdmin(admin.ModelAdmin):
    list_display = ('nome_empresa', 'cnpj', 'categoria', 'nome_contato')
    search_fields = ('nome_empresa', 'cnpj')
    list_filter = ('categoria',)


@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'quantidade',
                    'quantidade_minima', 'status_estoque')

    def status_estoque(self, obj):
        if obj.quantidade <= obj.quantidade_minima:
            return format_html('<span style="color: red;">●</span> Baixo Estoque')
        return format_html('<span style="color: green;">●</span> Normal')
    status_estoque.short_description = 'Status'
