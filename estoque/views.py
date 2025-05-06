import pandas as pd
from unidecode import unidecode
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import models
from django.db.models import Sum, Count, F, DateField
from .models import Produto, Movimentacao, Fornecedor, LogAtividade
from .forms import ProdutoForm, MovimentacaoForm, EditarPerfilForm
from django.contrib import messages
from .forms import ImportarProdutosForm, FornecedorForm
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse, reverse_lazy
from django.contrib.auth.models import User
from django.db.models.functions import Trunc


def home(request):
    return render(request, 'estoque/home.html')


@login_required
def lista_produtos(request):
    search_query = request.GET.get('q', '')
    sort_field = request.GET.get('sort', 'nome')
    sort_direction = request.GET.get('dir', 'asc')

    # Mapeamento seguro de campos para ordenação
    valid_fields = {'nome', 'quantidade', 'valor_unitario', 'categoria'}
    sort_field = sort_field if sort_field in valid_fields else 'nome'

    # Determina a direção da ordenação
    ordering = sort_field if sort_direction == 'asc' else f'-{sort_field}'

    produtos = Produto.objects.all().order_by(ordering)

    # Mantém a busca
    if search_query:
        produtos = produtos.filter(
            Q(nome__icontains=search_query) |
            Q(categoria__icontains=search_query)
        )

    return render(request, 'estoque/lista.html', {
        'produtos': produtos,
        'search_query': search_query,
        'current_sort': sort_field,
        'current_dir': sort_direction
    })


@login_required
def novo_produto(request):
    if request.method == 'POST':
        form = ProdutoForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('lista_produtos')
    else:
        form = ProdutoForm()
    return render(request, 'estoque/novo.html', {'form': form})


@login_required
def nova_movimentacao(request):
    if request.method == 'POST':
        form = MovimentacaoForm(request.POST)
        if form.is_valid():
            movimentacao = form.save()  # O signal será acionado aqui

            # Verifica estoque mínimo após movimentação
            if movimentacao.produto.quantidade <= movimentacao.produto.quantidade_minima:
                messages.warning(
                    request,
                    f"Atenção! O produto {movimentacao.produto.nome} \
                        está abaixo do estoque mínimo \
                            ({movimentacao.produto.quantidade_minima})"
                )

            return redirect('nova_movimentacao')
    else:
        form = MovimentacaoForm()

    return render(request, 'estoque/movimentacao.html', {'form': form})


@login_required
def editar_produto(request, produto_id):
    produto = get_object_or_404(Produto, id=produto_id)

    if request.method == 'POST':
        form = ProdutoForm(request.POST, request.FILES, instance=produto)
        if form.is_valid():
            produto = form.save()
            if produto.quantidade <= produto.quantidade_minima:
                messages.warning(
                    request, "Este produto está abaixo do estoque mínimo!")
        return redirect('lista_produtos')
    else:
        form = ProdutoForm(instance=produto)
    return render(request, 'estoque/editar_produtos.html', {'form': form})


@login_required
def excluir_produto(request, produto_id):
    produto = get_object_or_404(Produto, id=produto_id)
    if request.method == 'POST':
        produto.delete()
        return redirect('lista_produtos')
    return render(request, 'estoque/excluir_produtos.html',
                  {'produto': produto})


@login_required
def importar_produtos(request):
    context = {'form': ImportarProdutosForm()}  # Inicializa o contexto
    search_query = ""

    if request.method == 'POST':
        form = ImportarProdutosForm(request.POST, request.FILES)
        context['form'] = form

        try:
            if form.is_valid():
                print("\n--- INICIANDO IMPORTAÇÃO ---")
                df = pd.read_excel(request.FILES['arquivo_excel'])
                print("Planilha recebida:", df.columns.tolist())

                # Validação das colunas
                required_columns = ['Nome', 'Quantidade',
                                    'Valor Unitário', 'Categoria']
                if not all(col in df.columns for col in required_columns):
                    messages.error(request, "❌ Colunas obrigatórias ausentes!")
                    return render(request, 'estoque/importar_produtos.html',
                                  context)

                # Processamento
                success_count = 0
                errors = []  # Sempre inicializa a lista de erros

                for index, row in df.iterrows():
                    try:
                        # Validação básica
                        if pd.isna(row['Nome']) or pd.isna(row['Quantidade']):
                            raise ValueError("Campos obrigatórios em branco")

                        # Cria o produto
                        Produto.objects.create(
                            nome=str(row['Nome']),
                            quantidade=int(row['Quantidade']),
                            quantidade_minima=int(
                                row.get('Quantidade Mínima', 5)),
                            valor_unitario=float(row['Valor Unitário']),
                            categoria=str(row['Categoria'])
                        )
                        success_count += 1

                    except Exception as e:
                        errors.append({
                            'linha': index + 2,
                            'erro': str(e),
                            'dados': dict(row)
                        })
                        print(f"Erro na linha {index+2}: {str(e)}")

                # Resultados
                if errors:
                    context['errors'] = errors
                    context['success_count'] = success_count
                    print(
                        f"Importação parcial: {success_count} sucessos, {len(errors)} erros")
                else:
                    messages.success(
                        request,
                        f"✅ {success_count} produtos importados com sucesso!")
                    return redirect('lista_produtos')

            if success_count > 0:
                LogAtividade.objects.create(
                    usuario=request.user,
                    acao='I',
                    modelo_afetado='Produto',
                    detalhes=f"Importados {success_count} produtos"
                )

        except Exception as e:
            print("ERRO GRAVE:", str(e))
            messages.error(request, f"❌ Erro crítico: {str(e)}")
            return redirect('importar_produtos')

    return render(request, 'estoque/importar_produtos.html', context)


@login_required
def perfil_usuario(request):
    usuario = request.user
    return render(request, 'estoque/perfil.html', {'usuario': usuario})


@login_required
def editar_perfil(request):
    if request.method == 'POST':
        form = EditarPerfilForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('perfil')
    else:
        form = EditarPerfilForm(instance=request.user)

    return render(request, 'estoque/editar_perfil.html', {'form': form})


def buscar_autocomplete(request):
    termo = request.GET.get('term', '')
    termo_normalizado = unidecode(termo).lower()

    produtos = Produto.objects.filter(
        nome_normalizado__icontains=termo_normalizado
    ).values_list('nome', flat=True)[:10]

    return JsonResponse(list(produtos), safe=False)


@login_required
def analytics(request):
    periodo = request.GET.get('periodo', 'mensal')

    # Dados Gerais
    total_estoque = Produto.objects.aggregate(
        total=Sum('quantidade'))['total'] or 0
    produtos_baixo_estoque = Produto.objects.filter(
        quantidade__lte=F('quantidade_minima'))

    # Rotatividade
    rotatividade = Produto.objects.annotate(
        total_movimentos=Count('movimentacao')
    ).order_by('-total_movimentos')

    # Histórico por Período
    date_trunc = {
        'anual': Trunc('data', 'year'),
        'mensal': Trunc('data', 'month'),
        'quinzenal': Trunc('data', 'day')
    }.get(periodo, Trunc('data', 'month'))

    movimentacoes = Movimentacao.objects.annotate(
        periodo=date_trunc
    ).values('periodo', 'produto__nome').annotate(
        total=Sum('quantidade'),
        valor_total=Sum(F('quantidade') * F('preco_unitario'))
    )

    # Histórico de Compras
    historico_fornecedores = Movimentacao.objects.filter(
        tipo='entrada').values('fornecedor__nome_empresa').annotate(
        total_compras=Sum(F('quantidade') * F('preco_unitario'))
    ).order_by('-total_compras')

    return render(request, 'estoque/analytics.html', {
        'total_estoque': total_estoque,
        'produtos_baixo_estoque': produtos_baixo_estoque,
        'rotatividade': rotatividade,
        'movimentacoes': movimentacoes,
        'historico_fornecedores': historico_fornecedores,
        'periodo_selecionado': periodo
    })


@login_required
@user_passes_test(lambda u: u.is_superuser)  # Restringe a superusuários
def excluir_todos_produtos(request):
    if request.method == 'POST':
        try:
            # Confirmação adicional
            confirmacao = request.POST.get('confirmacao', '') == 'SIM'
            if confirmacao:
                Produto.objects.all().delete()
                messages.success(
                    request, "Todos os produtos foram excluídos com sucesso!")
                return redirect('lista_produtos')
            else:
                messages.error(request, "Confirmação inválida")
        except Exception as e:
            messages.error(request, f"Erro ao excluir produtos: {str(e)}")

    return render(request, 'estoque/confirmar_exclusao_total.html')


class FornecedorListView(LoginRequiredMixin, ListView):
    model = Fornecedor
    template_name = 'estoque/lista_fornecedores.html'
    context_object_name = 'fornecedores'


class FornecedorCreateView(LoginRequiredMixin, CreateView):
    model = Fornecedor
    form_class = FornecedorForm
    template_name = 'estoque/editar_fornecedor.html'
    success_url = reverse_lazy('lista_fornecedores')


class FornecedorUpdateView(LoginRequiredMixin, UpdateView):
    model = Fornecedor
    form_class = FornecedorForm
    template_name = 'estoque/editar_fornecedor.html'
    success_url = reverse_lazy('lista_fornecedores')


class FornecedorDeleteView(LoginRequiredMixin, DeleteView):
    model = Fornecedor
    template_name = 'estoque/confirmar_exclusao_fornecedor.html'
    success_url = reverse_lazy('lista_fornecedores')


class LogAtividadeListView(LoginRequiredMixin, ListView):
    model = LogAtividade
    template_name = 'estoque/logs.html'
    context_object_name = 'logs'
    paginate_by = 20

    def get_queryset(self):
        return LogAtividade.objects.select_related('usuario').order_by('-data_hora')

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_staff:
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)
