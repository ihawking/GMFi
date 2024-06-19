from datetime import timedelta

from celery import shared_task
from django.db.models import Q
from django.utils import timezone

from chains.models import Block, Transaction, PlatformTransaction
from common.decorators import singleton_task


@shared_task
def filter_and_store_tx(block_id, tx_metadata):
    block = Block.objects.get(pk=block_id)
    network = block.network

    if network.is_transaction_should_be_processed(tx_metadata):
        receipt = network.get_transaction_receipt(tx_hash=tx_metadata["hash"])
        Transaction.objects.create(
            hash=tx_metadata["hash"],
            block=block,
            transaction_index=tx_metadata["transactionIndex"],
            metadata=tx_metadata,
            receipt=receipt,
        )


@shared_task
@singleton_task(timeout=16)
def transact_platform_transactions():
    now = timezone.now()
    seconds_ago_600 = now - timedelta(seconds=600)

    for platform_tx in PlatformTransaction.objects.filter(
        Q(hash__isnull=True) | Q(hash__isnull=False, transaction__isnull=True, transacted_at__lt=seconds_ago_600)
    ).filter(account__tx_callable_failed_times__lt=32)[:4]:
        platform_tx.transact()


@shared_task
@singleton_task(timeout=32)
def confirm_past_blocks(block_id):
    latest_block = Block.objects.get(pk=block_id)

    for block in Block.objects.filter(
        network=latest_block.network,
        number__lte=max(1, latest_block.number - latest_block.network.block_confirmations_count),
        confirmed=False,
    ).order_by("number")[:8]:
        if block.confirm():
            for tx in Transaction.objects.filter(block=block):
                tx.confirm()
