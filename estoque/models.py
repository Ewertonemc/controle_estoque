from django.db import models
from unidecode import unidecode
from decimal import Decimal
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MinLengthValidator


class Produto(models.Model):
    imagem = models.ImageField(
        upload_to='produtos/',
        blank=True,
        null=True,
        verbose_name='Imagem do Produto'
    )
    quantidade_minima = models.IntegerField(
        default=5,  # Valor padrão
        verbose_name="Quantidade Mínima",
        help_text="Quantidade abaixo da qual o produto deve ser alertado"
    )
    nome = models.CharField(max_length=100)
    nome_normalizado = models.CharField(max_length=100, editable=False)
    quantidade = models.IntegerField(
        default=0, validators=[MinValueValidator(0)])
    valor_unitario = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0.00)]
    )
    categoria = models.CharField(max_length=50, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        self.nome_normalizado = unidecode(self.nome).lower()
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['nome']  # Ordenação padrão para todas as queries

    @property
    def valor_total(self):
        return self.quantidade * self.valor_unitario

    def __str__(self):
        return self.nome

    @classmethod
    def buscar(cls, termo):
        termo_normalizado = unidecode(termo).lower()
        return cls.objects.filter(
            Q(nome_normalizado__icontains=termo_normalizado) |
            Q(nome__icontains=termo)
        ).distinct()


class Fornecedor(models.Model):
    CATEGORIA_CHOICES = [
        ('SUBLIMACAO E TRANSFER', 'Sublimação e Transfer'),
        ('SUBLIMACAO', 'Sublimação'),
        ('TRANSFER', 'Transfer'),
        ('TECIDOS', 'Tecidos'),
        ('TODOS', 'Todos'),
    ]

    nome_empresa = models.CharField(
        max_length=100, verbose_name="Nome da Empresa")
    cnpj = models.CharField(
        max_length=18,
        unique=True,
        validators=[MinLengthValidator(14)],
        verbose_name="CNPJ"
    )
    telefone = models.CharField(max_length=15, verbose_name="Telefone")
    endereco = models.TextField(verbose_name="Endereço Completo")
    categoria = models.CharField(
        max_length=25,
        choices=CATEGORIA_CHOICES,
        verbose_name="Categoria de Produtos"
    )
    nome_contato = models.CharField(
        max_length=100, verbose_name="Nome do Contato")
    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nome_empresa


class Movimentacao(models.Model):
    TIPO_CHOICES = [('entrada', 'Entrada'), ('saida', "Saída")]

    produto = models.ForeignKey(Produto, on_delete=models.CASCADE)
    fornecedor = models.ForeignKey(
        Fornecedor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        default=None,
    )
    tipo = models.CharField(max_length=7, choices=TIPO_CHOICES)
    quantidade = models.IntegerField()
    data = models.DateTimeField(auto_now_add=True)
    preco_unitario = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
    )

    def __str__(self):
        return f"{self.tipo} - {self.produto.nome}"


class LogAtividade(models.Model):
    ACAO_CHOICES = [
        ('C', 'Criação'),
        ('E', 'Edição'),
        ('D', 'Exclusão'),
        ('I', 'Importação'),
    ]

    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    data_hora = models.DateTimeField(auto_now_add=True)
    acao = models.CharField(max_length=1, choices=ACAO_CHOICES)
    modelo_afetado = models.CharField(max_length=50)
    objeto_id = models.PositiveIntegerField()
    detalhes = models.TextField()

    def __str__(self):
        return f"{self.get_acao_display()} de {self.modelo_afetado} por {self.usuario}"

    class Meta:
        verbose_name = 'Log de Atividade'
        verbose_name_plural = 'Logs de Atividades'
        ordering = ['-data_hora']
