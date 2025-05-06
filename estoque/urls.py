from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
from .views import (
    FornecedorListView,
    FornecedorCreateView,
    FornecedorUpdateView,
    FornecedorDeleteView,
    LogAtividadeListView,
    excluir_todos_produtos
)

urlpatterns = [
    path('buscar-autocomplete/', views.buscar_autocomplete,
         name='buscar_autocomplete'),
    path('', views.home, name='home'),
    path('estoque/', views.lista_produtos, name='lista_produtos'),
    path('novo/', views.novo_produto, name='novo_produto'),
    path('movimentar/', views.nova_movimentacao, name='nova_movimentacao'),
    path('analytics/', views.analytics, name='analytics'),
    path('editar/<int:produto_id>/',
         views.editar_produto, name='editar_produto'),
    path('excluir/<int:produto_id>/',
         views.excluir_produto, name='excluir_produto'),
    path('importar/',
         views.importar_produtos, name='importar_produtos'),
    path('fornecedores/', FornecedorListView.as_view(),
         name='lista_fornecedores'),
    path('fornecedores/novo/', FornecedorCreateView.as_view(),
         name='novo_fornecedor'),
    path('fornecedores/editar/<int:pk>/',
         FornecedorUpdateView.as_view(), name='editar_fornecedor'),
    path('fornecedores/excluir/<int:pk>/',
         FornecedorDeleteView.as_view(), name='excluir_fornecedor'),
    path('logs/', LogAtividadeListView.as_view(), name='logs'),
    path('perfil/', views.perfil_usuario, name='perfil'),
    path('perfil/editar/', views.editar_perfil, name='editar_perfil'),
    path('produtos/excluir-todos/', excluir_todos_produtos,
         name='excluir_todos_produtos'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL,
                          document_root=settings.STATIC_ROOT)
