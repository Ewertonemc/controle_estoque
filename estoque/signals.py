from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db import transaction, models
from django.contrib.auth import get_user_model
from .models import Movimentacao, LogAtividade, Produto, Fornecedor
import logging

logger = logging.getLogger(__name__)
User = get_user_model()

# Atualiza o estoque


@receiver(post_save, sender=Movimentacao)
@transaction.atomic
def atualizar_estoque(sender, instance, **kwargs):
    try:
        produto = instance.produto
        logger.info(
            f"Iniciando atualização para \
                {produto.nome} - Tipo: {instance.tipo}")

        # Usar valores literais para comparação
        if instance.tipo == 'E':  # Entrada
            Produto.objects.filter(pk=produto.pk).update(
                quantidade=models.F('quantidade') + instance.quantidade
            )
        elif instance.tipo == 'S':  # Saída
            Produto.objects.filter(pk=produto.pk).update(
                quantidade=models.F('quantidade') - instance.quantidade
            )

        produto.refresh_from_db()
        logger.info(f"Estoque atualizado: {produto.quantidade}")

    except Exception as e:
        logger.error(f"Falha crítica: {str(e)}", exc_info=True)
        raise


def criar_log(sender, instance, acao):
    try:
        usuario = None
        if hasattr(instance, 'usuario'):
            usuario = instance.usuario
        elif hasattr(instance, 'user'):
            usuario = instance.user

        LogAtividade.objects.create(
            usuario=usuario,
            acao=acao,
            modelo_afetado=sender.__name__,
            objeto_id=instance.id,
            detalhes={
                'model': sender.__name__,
                'id': instance.id,
                'acao': acao,
                'dados': str(instance)
            }
        )
    except Exception as e:
        logger.error(f"Erro ao criar log: {str(e)}", exc_info=True)


@receiver(post_save, sender=Produto)
@receiver(post_save, sender=Fornecedor)
@receiver(post_save, sender=User)
def log_post_save(sender, instance, created, **kwargs):
    acao = 'C' if created else 'E'
    criar_log(sender, instance, acao)


@receiver(post_delete, sender=Produto)
@receiver(post_delete, sender=Fornecedor)
@receiver(post_delete, sender=User)
def log_post_delete(sender, instance, **kwargs):
    criar_log(sender, instance, 'D')
