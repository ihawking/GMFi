from celery import shared_task
from celery.exceptions import MaxRetriesExceededError
from django.db.models import Q
from chains.models import Block, Transaction, PlatformTransaction
from common.decorators import singleton_task
from common.utils.time import ago


@shared_task(bind=True, max_retries=64, time_limit=64, soft_time_limit=32)
def filter_and_store_tx(self, block_pk, tx_metadata):

    try:
        block = Block.objects.get(pk=block_pk)
        chain = block.chain
        if Transaction.objects.filter(hash=tx_metadata["hash"], block=block).exists():
            return

        if chain.is_transaction_should_be_processed(tx_metadata):
            receipt = chain.get_transaction_receipt(tx_hash=tx_metadata["hash"])
            Transaction.objects.create(
                hash=tx_metadata["hash"],
                block=block,
                transaction_index=tx_metadata["transactionIndex"],
                metadata=tx_metadata,
                receipt=receipt,
            )
    except Exception as exc:
        try:
            self.retry(exc=exc, countdown=min(2**self.request.retries, 3600))
        except MaxRetriesExceededError:
            pass


@shared_task(time_limit=64, soft_time_limit=32)
@singleton_task(timeout=64)
def transact_platform_transactions():
    for platform_tx in PlatformTransaction.objects.filter(
        Q(transacted_at__isnull=True) | Q(transacted_at__lt=ago(minutes=16), transaction__isnull=True)
    ).filter(account__tx_callable_failed_times__lt=32, created_at__lt=ago(seconds=4))[:8]:
        platform_tx.check_tx()


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
