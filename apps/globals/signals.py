from django.db import transaction as db_transaction

from chains.models import Account
from common.utils.crypto import generate_random_code
from globals.models import Project


def create_global_project(sender, **kwargs):
    try:
        Project.objects.get(id=1)

    except Project.DoesNotExist:
        with db_transaction.atomic():
            Project.objects.create(
                id=1,
                system_account=Account.generate(),
                hmac_key=generate_random_code(length=32),
            )
