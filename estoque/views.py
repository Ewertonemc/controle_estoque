import logging
from django.db import transaction
from django.http import JsonResponse, HttpRequest, HttpResponse
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views import View
from django.views.generic import (
    ListView, CreateView, UpdateView, DeleteView, TemplateView
)
from django.urls import reverse_lazy
from django.db.models import (
    Q, F, Sum, Count, DateField
)
from django.db.models.functions import Trunc
from unidecode import unidecode
import pandas as pd

from .models import Produto, Movimentacao, Fornecedor, LogAtividade
from .forms import (
    ProdutoForm, MovimentacaoForm, EditarPerfilForm,
    ImportarProdutosForm, FornecedorForm
)
from .services import ImportadorProdutos

logger = logging.getLogger(__name__)

# Verifica tipo de usuário, para saber suas permissões


class SuperUserRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_superuser

# Página inicial


class HomeView(View):
    def get(self, request: HttpRequest) -> HttpResponse:
        return render(request, 'estoque/home.html')

# Lista de Produtos


class ProdutoListView(LoginRequiredMixin, ListView):
    model = Produto
    template_name = 'estoque/lista.html'
    context_object_name = 'produtos'
    paginate_by = 20
    ordering = 'nome'

    VALID_SORT_FIELDS = {'nome', 'quantidade', 'valor_unitario', 'categoria'}

    def get_queryset(self):
        queryset = super().get_queryset()
        search_query = self.request.GET.get('q', '')
        sort_field = self.request.GET.get('sort', self.ordering)
        sort_direction = self.request.GET.get('dir', 'asc')

        # Filtro
        if search_query:
            queryset = queryset.filter(
                Q(nome__icontains=search_query) |
                Q(categoria__icontains=search_query)
            )

        # Ordenação
        if sort_field in self.VALID_SORT_FIELDS:
            if sort_direction == 'desc':
                sort_field = f'-{sort_field}'
            return queryset.order_by(sort_field)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'search_query': self.request.GET.get('q', ''),
            'current_sort': self.request.GET.get('sort', self.ordering),
            'current_dir': self.request.GET.get('dir', 'asc')
        })
        return context

# Novo Produto


class ProdutoCreateView(LoginRequiredMixin, CreateView):
    model = Produto
    form_class = ProdutoForm
    template_name = 'estoque/novo.html'
    success_url = reverse_lazy('lista_produtos')

    def form_valid(self, form):
        form.instance.usuario = self.request.user
        return super().form_valid(form)

# Para editar os produtos


class ProdutoUpdateView(LoginRequiredMixin, UpdateView):
    model = Produto
    form_class = ProdutoForm
    template_name = 'estoque/editar_produtos.html'
    success_url = reverse_lazy('lista_produtos')

    def form_valid(self, form):
        response = super().form_valid(form)
        if self.object.quantidade <= self.object.quantidade_minima:
            messages.warning(
                self.request, "Este produto está abaixo do estoque mínimo!")
        return response

# Para exclusão dos produtos


class ProdutoDeleteView(LoginRequiredMixin, DeleteView):
    model = Produto
    template_name = 'estoque/excluir_produtos.html'
    success_url = reverse_lazy('lista_produtos')

# Para fazer a movimentação dos produtos


class MovimentacaoCreateView(LoginRequiredMixin, CreateView):
    model = Movimentacao
    form_class = MovimentacaoForm
    template_name = 'estoque/movimentacao.html'
    success_url = reverse_lazy('nova_movimentacao')

    def form_valid(self, form):
        form.instance.usuario = self.request.user
        messages.success(
            self.request,
            f"Movimentação de {form.cleaned_data['quantidade']} \
                unidades registrada!"
        )
        return super().form_valid(form)

# Importar produtos de uma planilha de excel


class ImportarProdutosView(LoginRequiredMixin, View):
    template_name = 'estoque/importar_produtos.html'
    form_class = ImportarProdutosForm

    def get(self, request: HttpRequest) -> HttpResponse:
        return render(request, self.template_name, {'form': self.form_class()})

    @transaction.atomic
    def post(self, request: HttpRequest) -> HttpResponse:
        form = self.form_class(request.POST, request.FILES)
        context = {'form': form}

        if not form.is_valid():
            return render(request, self.template_name, context)

        try:
            importador = ImportadorProdutos(request.FILES['arquivo_excel'])
            result = importador.executar(request.user)

            if result['errors']:
                context.update({
                    'errors': result['errors'],
                    'success_count': result['success_count']
                })
                messages.warning(
                    request,
                    f"Importação parcial: {result['success_count']} sucessos, "
                    f"{len(result['errors'])} erros"
                )
            else:
                messages.success(
                    request,
                    f"✅ {result['success_count']} \
                        produtos importados com sucesso!"
                )
                return redirect('lista_produtos')

        except Exception as e:
            logger.error(f"Erro na importação: {str(e)}", exc_info=True)
            messages.error(request, f"❌ Erro crítico: {str(e)}")

        return render(request, self.template_name, context)

# Para relatórios


class AnalyticsView(LoginRequiredMixin, TemplateView):
    template_name = 'estoque/analytics.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        periodo = self.request.GET.get('periodo', 'mensal')

        # Dados Gerais
        context['total_estoque'] = Produto.objects.aggregate(
            total=Sum('quantidade'))['total'] or 0
        context['produtos_baixo_estoque'] = Produto.objects.filter(
            quantidade__lte=F('quantidade_minima'))

        # Rotatividade corrigida
        context['rotatividade'] = Produto.objects.annotate(
            total_movimentos=Count('movimentacoes')
        ).order_by('-total_movimentos')

        # Definir a função de truncagem corretamente
        trunc_kwargs = {
            'anual': ('year', 'Ano'),
            'mensal': ('month', 'Mês'),
            'quinzenal': ('day', 'Dia')
        }.get(periodo, ('month', 'Mês'))

        # Histórico por Período
        movimentacoes = Movimentacao.objects.annotate(
            periodo=Trunc('data', trunc_kwargs[0], output_field=DateField())
        ).values('periodo').annotate(
            total=Sum('quantidade'),
            valor_total=Sum(F('quantidade') * F('preco_unitario'))
        ).order_by('periodo')

        # Preparar dados para o gráfico
        context['chart_labels'] = [m['periodo'].strftime(
            '%Y-%m-%d') for m in movimentacoes]
        context['chart_data'] = [m['total'] for m in movimentacoes]

        # Histórico de Compras
        context['historico_fornecedores'] = Movimentacao.objects.filter(
            tipo=Movimentacao.TipoMovimentacao.ENTRADA
        ).values('fornecedor__nome_empresa').annotate(
            total_compras=Sum(F('quantidade') * F('preco_unitario'))
        ).order_by('-total_compras')

        context['periodo_selecionado'] = periodo

        return context

# Exclusão de todos os produtos


class ExcluirTodosProdutosView(SuperUserRequiredMixin, View):
    template_name = 'estoque/confirmar_exclusao_total.html'

    def post(self, request: HttpRequest) -> HttpResponse:
        if request.POST.get('confirmacao') == 'SIM':
            Produto.objects.all().delete()
            messages.success(request, "Todos os produtos foram excluídos!")
            return redirect('lista_produtos')

        messages.error(request, "Confirmação inválida")
        return redirect('home')

# Lista de fornecedores


class FornecedorListView(LoginRequiredMixin, ListView):
    model = Fornecedor
    template_name = 'estoque/lista_fornecedores.html'
    context_object_name = 'fornecedores'

# Cadastro de fornecedores


class FornecedorCreateView(LoginRequiredMixin, CreateView):
    model = Fornecedor
    form_class = FornecedorForm
    template_name = 'estoque/editar_fornecedor.html'
    success_url = reverse_lazy('lista_fornecedores')

# Atualizar fornecedores


class FornecedorUpdateView(LoginRequiredMixin, UpdateView):
    model = Fornecedor
    form_class = FornecedorForm
    template_name = 'estoque/editar_fornecedor.html'
    success_url = reverse_lazy('lista_fornecedores')

# Deletar Fornecedores


class FornecedorDeleteView(LoginRequiredMixin, DeleteView):
    model = Fornecedor
    template_name = 'estoque/confirmar_exclusao_fornecedor.html'
    success_url = reverse_lazy('lista_fornecedores')

# Perfil de usuários


class PerfilUsuarioView(LoginRequiredMixin, View):
    def get(self, request: HttpRequest) -> HttpResponse:
        return render(request, 'estoque/perfil.html', {'usuario': request.user})

# Editar perfil dos usuários


class EditarPerfilView(LoginRequiredMixin, UpdateView):
    form_class = EditarPerfilForm
    template_name = 'estoque/editar_perfil.html'
    success_url = reverse_lazy('perfil')

    def get_object(self):
        return self.request.user


@login_required
def buscar_autocomplete(request: HttpRequest) -> JsonResponse:
    termo = request.GET.get('term', '')
    termo_normalizado = unidecode(termo).lower()

    produtos = Produto.objects.filter(
        nome_normalizado__icontains=termo_normalizado
    ).values_list('nome', flat=True)[:10]

    return JsonResponse(list(produtos), safe=False)

# Lista com as ações ocorridas, por usuários


class LogAtividadeListView(LoginRequiredMixin, ListView):
    model = LogAtividade
    template_name = 'estoque/logs.html'
    context_object_name = 'logs'
    paginate_by = 50

    def get_queryset(self):
        return LogAtividade.objects.select_related('usuario').order_by('-data_hora')

    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        if not request.user.is_staff:
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)
