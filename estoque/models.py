from django.db import models
from django.db.models import Q, Index
from unidecode import unidecode
from django.contrib.auth.models import User
from django.core.validators import (
    MinValueValidator,
    MinLengthValidator,
    RegexValidator
)
from django.utils.translation import gettext_lazy as _


class Produto(models.Model):
    class CategoriaProduto(models.TextChoices):
        TECIDOS = 'TECIDOS', _('Tecidos')
        SUBLIMACAO = 'SUBLIMAÇÃO', _('Sublimação')
        TRANSFER = 'TRANSFER', _('Transfer')
        OUTROS = 'OUTROS', _('Outros')

    imagem = models.ImageField(
        upload_to='produtos/',
        blank=True,
        null=True,
        verbose_name=_('Imagem do Produto'),
        help_text=_('Imagem representativa do produto')
    )
    nome = models.CharField(
        max_length=100,
        verbose_name=_('Nome'),
        db_index=True
    )
    nome_normalizado = models.CharField(
        max_length=100,
        editable=False,
        db_index=True
    )
    quantidade = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name=_('Quantidade em Estoque')
    )
    quantidade_minima = models.IntegerField(
        default=5,
        validators=[MinValueValidator(1)],
        verbose_name=_('Quantidade Mínima'),
        help_text=_('Nível mínimo para alertas de reabastecimento')
    )
    valor_unitario = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0.00)],
        verbose_name=_('Valor Unitário')
    )
    categoria = models.CharField(
        max_length=10,
        choices=CategoriaProduto.choices,
        default=CategoriaProduto.OUTROS,
        verbose_name=_('Categoria')
    )
    criado_em = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Data de Criação')
    )
    atualizado_em = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Última Atualização')
    )

    class Meta:
        verbose_name = _('Produto')
        verbose_name_plural = _('Produtos')
        ordering = ['nome']
        indexes = [
            Index(fields=['nome_normalizado']),
            Index(fields=['categoria', 'quantidade']),
        ]
        constraints = [
            models.CheckConstraint(
                check=Q(quantidade__gte=0),
                name='quantidade_nao_negativa'
            ),
            models.CheckConstraint(
                check=Q(quantidade_minima__gte=1),
                name='quantidade_minima_positiva'
            ),
        ]

    def __str__(self):
        return f"{self.nome} ({self.get_categoria_display()})"

    def save(self, *args, **kwargs):
        if not self.nome_normalizado or self.nome_changed():
            self.nome_normalizado = unidecode(self.nome).lower()
        super().save(*args, **kwargs)

    def nome_changed(self):
        if not self.pk:
            return True
        original = Produto.objects.get(pk=self.pk)
        return original.nome != self.nome

    @property
    def valor_total_estoque(self):
        return self.quantidade * self.valor_unitario

    @property
    def estoque_baixo(self):
        return self.quantidade <= self.quantidade_minima

    @classmethod
    def buscar(cls, termo):
        termo_normalizado = unidecode(termo).lower()
        return cls.objects.filter(
            Q(nome_normalizado__icontains=termo_normalizado) |
            Q(nome__icontains=termo)
        ).distinct()


class Fornecedor(models.Model):
    class CategoriaFornecedor(models.TextChoices):
        SUBLIMACAO_TRANSFER = 'SUB_TRANS', _('Sublimação e Transfer')
        SUBLIMACAO = 'SUB', _('Sublimação')
        TRANSFER = 'TRANS', _('Transfer')
        TECIDOS = 'TEC', _('Tecidos')
        GERAL = 'GERAL', _('Todos')

    nome_empresa = models.CharField(
        max_length=100,
        verbose_name=_('Razão Social'),
        db_index=True
    )
    cnpj = models.CharField(
        max_length=18,
        unique=True,
        validators=[
            MinLengthValidator(14),
            RegexValidator(
                r'^\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}$',
                _('Formato de CNPJ inválido')
            )
        ],
        verbose_name=_('CNPJ')
    )
    telefone = models.CharField(
        max_length=15,
        validators=[
            RegexValidator(
                r'^\+?1?\d{9,15}$',
                _('Formato de telefone inválido')
            )
        ],
        verbose_name=_('Telefone')
    )
    endereco = models.TextField(verbose_name=_('Endereço Completo'))
    categoria = models.CharField(
        max_length=9,
        choices=CategoriaFornecedor.choices,
        default=CategoriaFornecedor.GERAL,
        verbose_name=_('Categoria'),
        db_index=True
    )
    nome_contato = models.CharField(
        max_length=100,
        verbose_name=_('Responsável'))
    email = models.EmailField(
        blank=True,
        verbose_name=_('E-mail de Contato'))
    ativo = models.BooleanField(
        default=True,
        verbose_name=_('Ativo'))
    criado_em = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Data de Cadastro'))

    class Meta:
        verbose_name = _('Fornecedor')
        verbose_name_plural = _('Fornecedores')
        ordering = ['nome_empresa']
        indexes = [
            Index(fields=['categoria', 'ativo']),
        ]

    def __str__(self):
        # type: ignore
        return f"{self.nome_empresa} ({self.get_categoria_display()})"


class Movimentacao(models.Model):
    class TipoMovimentacao(models.TextChoices):
        ENTRADA = 'E', _('Entrada')
        SAIDA = 'S', _('Saída')

    produto = models.ForeignKey(
        Produto,
        on_delete=models.CASCADE,
        related_name='movimentacoes',
        verbose_name=_('Produto')
    )
    fornecedor = models.ForeignKey(
        Fornecedor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='movimentacoes',
        verbose_name=_('Fornecedor')
    )
    tipo = models.CharField(
        max_length=1,
        choices=TipoMovimentacao.choices,
        verbose_name=_('Tipo de Movimentação'),
        db_index=True
    )
    quantidade = models.IntegerField(
        validators=[MinValueValidator(1)],
        verbose_name=_('Quantidade')
    )
    preco_unitario = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        verbose_name=_('Preço Unitário')
    )
    data = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Data/Hora'),
        db_index=True
    )
    usuario = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=_('Responsável')
    )

    class Meta:
        verbose_name = _('Movimentação')
        verbose_name_plural = _('Movimentações')
        ordering = ['-data']
        indexes = [
            Index(fields=['tipo', 'data']),
        ]
        constraints = [
            models.CheckConstraint(
                check=Q(quantidade__gt=0),
                name='quantidade_movimentacao_positiva'
            ),
        ]

    def __str__(self):
        return f"{self.get_tipo_display()} \
            {self.quantidade} x {self.produto.nome}"

    @property
    def valor_total(self):
        return self.quantidade * self.preco_unitario


class LogAtividade(models.Model):
    class Acao(models.TextChoices):
        CRIACAO = 'C', _('Criação')
        EDICAO = 'E', _('Edição')
        EXCLUSAO = 'D', _('Exclusão')
        IMPORTACAO = 'I', _('Importação')

    usuario = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=_('Usuário')
    )
    data_hora = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Data/Hora'),
        db_index=True
    )
    acao = models.CharField(
        max_length=1,
        choices=Acao.choices,
        verbose_name=_('Ação')
    )
    modelo_afetado = models.CharField(
        max_length=50,
        verbose_name=_('Modelo Afetado'))
    objeto_id = models.CharField(
        max_length=36,  # Suporta UUIDs
        verbose_name=_('ID do Objeto'))
    detalhes = models.JSONField(
        default=dict,
        verbose_name=_('Detalhes Técnicos'))
    descricao = models.TextField(
        blank=True,
        verbose_name=_('Descrição Humana'))

    class Meta:
        verbose_name = _('Log de Atividade')
        verbose_name_plural = _('Logs de Atividades')
        ordering = ['-data_hora']
        indexes = [
            Index(fields=['modelo_afetado', 'acao']),
        ]

    def __str__(self):
        return f"{self.get_acao_display()} - \
            {self.modelo_afetado} #{self.objeto_id}"

    def save(self, *args, **kwargs):
        if not self.descricao:
            self.descricao = self._gerar_descricao()
        super().save(*args, **kwargs)

    def _gerar_descricao(self):
        return f"{self.usuario or 'Sistema'} realizou \
            {self.get_acao_display().lower()} em {self.modelo_afetado}"
