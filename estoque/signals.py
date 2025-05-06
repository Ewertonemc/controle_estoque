from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Movimentacao, LogAtividade, Produto, Fornecedor
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Movimentacao)
def atualizar_estoque(sender, instance, **kwargs):
    produto = instance.produto
    logger.info(f"Atualizando estoque do produto {produto.nome}...")

    try:
        if instance.tipo == 'entrada':
            produto.quantidade += instance.quantidade
        else:
            if produto.quantidade >= instance.quantidade:
                produto.quantidade -= instance.quantidade
            else:
                logger.error("Quantidade insuficiente em estoque!")
                return

        produto.save()
        logger.info(f"Estoque atualizado: {produto.quantidade}")

    except Exception as e:
        logger.error(f"Erro ao atualizar estoque: {str(e)}")


def criar_log(instance, acao, request=None):
    user = None
    if request and hasattr(request, 'user'):
        user = request.user if request.user.is_authenticated else None

    LogAtividade.objects.create(
        usuario=user,
        acao=acao,
        modelo_afetado=instance.__class__.__name__,
        objeto_id=instance.id,
        detalhes=str(instance)
    )


@receiver(post_save)
def log_post_save(sender, instance, created, **kwargs):
    if sender not in [Produto, Fornecedor, User]:
        return

    acao = 'C' if created else 'E'
    criar_log(instance, acao)


@receiver(post_delete)
def log_post_delete(sender, instance, **kwargs):
    if sender not in [Produto, Fornecedor, User]:
        return

    criar_log(instance, 'D')
