from celery import shared_task
from celery.exceptions import MaxRetriesExceededError
from django.db.models import Q
from chains.models import Block, Transaction, TransactionQueue
from common.decorators import singleton_task
from common.utils.time import ago
from django.db import transaction as db_transaction


@shared_task(bind=True, max_retries=64, time_limit=64, soft_time_limit=32)
def filter_and_store_tx(self, block_pk, tx_metadata):
    try:
        with db_transaction.atomic():
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
            self.retry(exc=exc, countdown=min(2**self.request.retries, 1800))
        except MaxRetriesExceededError:
            pass


@shared_task(time_limit=64, soft_time_limit=32)
@singleton_task(timeout=64)
def transact_platform_transactions():
    for transaction_queue in TransactionQueue.objects.filter(
        Q(transacted_at__isnull=True) | Q(transacted_at__lt=ago(minutes=16), transaction__isnull=True)
    ).filter(account__tx_callable_failed_times__lt=32, created_at__lt=ago(seconds=4))[:8]:
        transaction_queue.transact()


@shared_task(time_limit=64, soft_time_limit=32)
@singleton_task(timeout=64, use_params=True)
@db_transaction.atomic
def confirm_past_blocks(chain_pk):
    latest_block = Block.objects.filter(chain__pk=chain_pk).first()

    for block in Block.objects.filter(
        chain=latest_block.chain,
        number__lte=max(1, latest_block.number - latest_block.chain.block_confirmations_count),
        confirmed=False,
    ).order_by("number")[:32]:
        if block.confirm():
            for tx in Transaction.objects.filter(block=block):
                tx.confirm()
