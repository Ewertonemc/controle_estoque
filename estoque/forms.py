from django import forms
from django.core.validators import FileExtensionValidator, MinValueValidator
from django.contrib.auth.forms import UserChangeForm
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from .models import Produto, Movimentacao, Fornecedor


class ProdutoForm(forms.ModelForm):
    quantidade_minima = forms.IntegerField(
        min_value=1,
        initial=5,
        help_text="Quantidade mínima para alertas de estoque baixo"
    )

    class Meta:
        model = Produto
        fields = [
            'imagem', 'nome', 'quantidade',
            'quantidade_minima', 'valor_unitario', 'categoria'
        ]
        labels = {
            'quantidade_minima': _('Estoque Mínimo'),
            'valor_unitario': _('Preço Unitário (R$)')
        }
        help_texts = {
            'quantidade_minima': _(
                'Quantidade mínima para alertas de reposição'),
            'categoria': _('Classificação do produto')
        }
        widgets = {
            'valor_unitario': forms.NumberInput(attrs={'step': '0.01'}),
            'quantidade': forms.NumberInput(attrs={'min': '0'}),
            'quantidade_minima': forms.NumberInput(attrs={'min': '1'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['quantidade_minima'].required = True


class MovimentacaoForm(forms.ModelForm):
    tipo = forms.ChoiceField(
        choices=Movimentacao.TipoMovimentacao.choices,
        widget=forms.RadioSelect,
        label='Tipo'
    )

    class Meta:
        model = Movimentacao
        fields = ['produto', 'tipo', 'quantidade',
                  'preco_unitario', 'fornecedor']
        labels = {
            'preco_unitario': _('Preço Unitário (R$)'),
            'fornecedor': _('Fornecedor (opcional)')
        }
        widgets = {
            'produto': forms.Select(attrs={'class': 'form-select'}),
            'quantidade': forms.NumberInput(
                attrs={'min': '1', 'class': 'form-control'}),
            'preco_unitario': forms.NumberInput(
                attrs={'step': '0.01', 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['fornecedor'].required = False

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get('tipo') == Movimentacao.TipoMovimentacao.ENTRADA:
            if not cleaned_data.get('fornecedor'):
                self.add_error('fornecedor', _(
                    'Fornecedor obrigatório para entrada'))
        return cleaned_data


class ImportarProdutosForm(forms.Form):
    arquivo_excel = forms.FileField(
        label=_("Arquivo Excel"),
        validators=[
            FileExtensionValidator(
                allowed_extensions=['xlsx'],
                message=_("Apenas arquivos .xlsx são permitidos!")
            )
        ],
        help_text=_(
            "Formato esperado: Colunas devem conter "
            "Nome, Quantidade, Valor Unitário, Categoria"
        ),
        widget=forms.FileInput(attrs={'accept': '.xlsx'})
    )

    def clean_arquivo_excel(self):
        file = self.cleaned_data['arquivo_excel']
        if file.content_type not in [
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'application/octet-stream'
        ]:
            raise forms.ValidationError(_("Tipo de arquivo inválido"))
        return file


class FornecedorForm(forms.ModelForm):
    class Meta:
        model = Fornecedor
        fields = '__all__'
        exclude = ['ativo']
        labels = {
            'cnpj': _('CNPJ (XX.XXX.XXX/XXXX-XX)'),
            'categoria': _('Especialização')
        }
        widgets = {
            'endereco': forms.Textarea(attrs={'rows': 3, 'class': 'materialize-textarea'}),
            'telefone': forms.TextInput(attrs={'pattern': '[\+0-9\s\-\(\)]+'}),
            'categoria': forms.Select(attrs={'class': 'browser-default'})
        }

    def clean_cnpj(self):
        cnpj = self.cleaned_data['cnpj']
        if Fornecedor.objects.filter(cnpj=cnpj).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError(_("CNPJ já cadastrado"))
        return cnpj


class EditarPerfilForm(UserChangeForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']
        exclude = ['password']
        labels = {
            'username': _('Usuário'),
            'email': _('E-mail'),
            'first_name': _('Nome'),
            'last_name': _('Sobrenome')
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].required = True
