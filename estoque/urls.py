from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views
from .views import (
    HomeView,
    ProdutoListView,
    ProdutoCreateView,
    ProdutoUpdateView,
    ProdutoDeleteView,
    MovimentacaoCreateView,
    AnalyticsView,
    ImportarProdutosView,
    FornecedorListView,
    FornecedorCreateView,
    FornecedorUpdateView,
    FornecedorDeleteView,
    LogAtividadeListView,
    ExcluirTodosProdutosView,
    PerfilUsuarioView,
    EditarPerfilView
)

urlpatterns = [
    # Autocomplete
    path('buscar-autocomplete/', views.buscar_autocomplete,
         name='buscar_autocomplete'),

    # Home
    path('', HomeView.as_view(), name='home'),

    # Produtos
    path('estoque/', ProdutoListView.as_view(), name='lista_produtos'),
    path('novo/', ProdutoCreateView.as_view(), name='novo_produto'),
    path('editar/<int:pk>/', ProdutoUpdateView.as_view(),
         name='editar_produto'),
    path('excluir/<int:pk>/', ProdutoDeleteView.as_view(),
         name='excluir_produto'),
    path('produtos/excluir-todos/', ExcluirTodosProdutosView.as_view(),
         name='excluir_todos_produtos'),

    # Movimentações
    path('movimentar/', MovimentacaoCreateView.as_view(),
         name='nova_movimentacao'),

    # Analytics
    path('analytics/', AnalyticsView.as_view(), name='analytics'),

    # Importação
    path('importar/', ImportarProdutosView.as_view(),
         name='importar_produtos'),

    # Fornecedores
    path('fornecedores/', FornecedorListView.as_view(),
         name='lista_fornecedores'),
    path('fornecedores/novo/', FornecedorCreateView.as_view(),
         name='novo_fornecedor'),
    path('fornecedores/editar/<int:pk>/',
         FornecedorUpdateView.as_view(), name='editar_fornecedor'),
    path('fornecedores/excluir/<int:pk>/',
         FornecedorDeleteView.as_view(), name='excluir_fornecedor'),

    # Logs
    path('logs/', LogAtividadeListView.as_view(), name='logs'),

    # Perfil
    path('perfil/', PerfilUsuarioView.as_view(), name='perfil'),
    path('perfil/editar/', EditarPerfilView.as_view(), name='editar_perfil'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL,
                          document_root=settings.STATIC_ROOT)
