import pandas as pd
from django.db import transaction
from .models import Produto, LogAtividade
import logging

logger = logging.getLogger(__name__)


class ImportadorProdutos:
    """Serviço para importação de produtos via Excel"""

    REQUIRED_COLUMNS = ['Nome', 'Quantidade', 'Valor Unitário', 'Categoria']
    DEFAULT_MIN_STOCK = 5

    def __init__(self, arquivo):
        self.df = pd.read_excel(arquivo)
        self.errors = []
        self.success_count = 0

    def validar_colunas(self):
        return all(col in self.df.columns for col in self.REQUIRED_COLUMNS)

    @transaction.atomic
    def executar(self, usuario):
        """Executa a importação com registro de logs"""
        for index, row in self.df.iterrows():
            try:
                self._processar_linha(row, index+2)
            except Exception as e:
                self._registrar_erro(row, index+2, str(e))

        if self.success_count > 0:
            LogAtividade.objects.create(
                usuario=usuario,
                acao='I',
                modelo_afetado='Produto',
                detalhes=f"Importados {self.success_count} produtos"
            )

        return {
            'success_count': self.success_count,
            'errors': self.errors
        }

    def _processar_linha(self, row, linha_num):
        """Processa uma linha individual do Excel"""
        # Validação de campos obrigatórios
        if any(pd.isna(row[col]) for col in self.REQUIRED_COLUMNS):
            raise ValueError("Campos obrigatórios ausentes")

        # Validação de tipos
        if not isinstance(row['Quantidade'], (int, float)):
            raise ValueError("Quantidade deve ser numérica")

        # Criação do produto
        Produto.objects.create(
            nome=str(row['Nome']),
            quantidade=int(row['Quantidade']),
            quantidade_minima=int(
                row.get('Quantidade Mínima', self.DEFAULT_MIN_STOCK)),
            valor_unitario=float(row['Valor Unitário']),
            categoria=str(row['Categoria'])
        )
        self.success_count += 1

    def _registrar_erro(self, row, linha_num, erro):
        """Registra erros de processamento"""
        self.errors.append({
            'linha': linha_num,
            'erro': erro,
            'dados': dict(row.dropna().astype(str))
        })
        logger.error(f"Erro na linha {linha_num}: {erro}")
