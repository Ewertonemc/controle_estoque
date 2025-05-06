from django import forms
from .models import Produto, Movimentacao, Fornecedor
from django.core.validators import FileExtensionValidator
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserChangeForm


class ProdutoForm(forms.ModelForm):
    class Meta:
        model = Produto
        fields = ['imagem', 'nome', 'quantidade', 'quantidade_minima',
                  'valor_unitario', 'categoria']


class MovimentacaoForm(forms.ModelForm):
    class Meta:
        model = Movimentacao
        fields = ['produto', 'tipo', 'quantidade']


class ImportarProdutosForm(forms.Form):
    arquivo_excel = forms.FileField(
        label="Selecione a planilha",
        validators=[
            FileExtensionValidator(
                allowed_extensions=['xlsx'],
                message="Apenas arquivos .xlsx são permitidos!"
            )
        ],
        help_text="Formato esperado: XLSX com colunas: "
        "Nome, Quantidade, Quantidade Mínima, Valor Unitário, Categoria"
    )


class FornecedorForm(forms.ModelForm):
    class Meta:
        model = Fornecedor
        fields = '__all__'
        widgets = {
            'endereco': forms.Textarea(attrs={'rows': 3}),
        }


class EditarPerfilForm(UserChangeForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']
