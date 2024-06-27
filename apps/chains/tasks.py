from celery import shared_task
from django.db.models import Q

from chains.models import Block, Transaction, PlatformTransaction
from common.decorators import singleton_task
from common.utils.time import ago


@shared_task(time_limit=64, soft_time_limit=32)
def filter_and_store_tx(block_pk, tx_metadata):
    block = Block.objects.get(pk=block_pk)
    chain = block.chain

    if chain.is_transaction_should_be_processed(tx_metadata):
        receipt = chain.get_transaction_receipt(tx_hash=tx_metadata["hash"])
        Transaction.objects.create(
            hash=tx_metadata["hash"],
            block=block,
            transaction_index=tx_metadata["transactionIndex"],
            metadata=tx_metadata,
            receipt=receipt,
        )


@shared_task(time_limit=64, soft_time_limit=32)
@singleton_task(timeout=64)
def transact_platform_transactions():
    # 要创建超过4s，防止回滚
    for platform_tx in PlatformTransaction.objects.filter(
        Q(hash__isnull=True) | Q(transacted_at__lt=ago(minutes=10), transaction__isnull=True)
    ).filter(account__tx_callable_failed_times__lt=32, created_at__lt=ago(4))[:4]:
        platform_tx.transact()


@shared_task(time_limit=64, soft_time_limit=32)
@singleton_task(timeout=32)
def confirm_past_blocks(block_id):
    latest_block = Block.objects.get(pk=block_id)

    for block in Block.objects.filter(
        chain=latest_block.chain,
        number__lte=max(1, latest_block.number - latest_block.chain.block_confirmations_count),
        confirmed=False,
    ).order_by("number")[:8]:
        if block.confirm():
            for tx in Transaction.objects.filter(block=block):
                tx.confirm()
