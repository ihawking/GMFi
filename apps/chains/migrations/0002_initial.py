# Generated by Django 5.0.6 on 2024-06-29 05:01

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("chains", "0001_initial"),
        ("tokens", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="chain",
            name="currency",
            field=models.ForeignKey(
                blank=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="chains_as_currency",
                to="tokens.token",
                verbose_name="原生代币",
            ),
        ),
        migrations.AddField(
            model_name="block",
            name="chain",
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="chains.chain"),
        ),
        migrations.AddField(
            model_name="transaction",
            name="block",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, related_name="transactions", to="chains.block"
            ),
        ),
        migrations.AddField(
            model_name="transactionqueue",
            name="account",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT, to="chains.account", verbose_name="账户"
            ),
        ),
        migrations.AddField(
            model_name="transactionqueue",
            name="chain",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.DO_NOTHING, to="chains.chain", verbose_name="网络"
            ),
        ),
        migrations.AddField(
            model_name="transactionqueue",
            name="transaction",
            field=models.OneToOneField(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="transaction_queue",
                to="chains.transaction",
                verbose_name="交易",
            ),
        ),
        migrations.AlterUniqueTogether(
            name="block",
            unique_together={("chain", "number")},
        ),
        migrations.AlterUniqueTogether(
            name="transactionqueue",
            unique_together={("account", "chain", "nonce")},
        ),
    ]
