# Generated by Django 5.0.6 on 2024-06-25 15:12

import common.fields
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Account",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "address",
                    common.fields.ChecksumAddressField(db_index=True, max_length=42, unique=True, verbose_name="地址"),
                ),
                ("encrypted_private_key", models.TextField()),
                ("tx_callable_failed_times", models.PositiveIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="创建时间")),
            ],
            options={
                "verbose_name": "本地账户",
                "verbose_name_plural": "本地账户",
                "ordering": ("-created_at",),
            },
        ),
        migrations.CreateModel(
            name="Network",
            fields=[
                (
                    "chain_id",
                    models.PositiveIntegerField(
                        blank=True,
                        help_text="根据RPC自动检测Chain ID，无需填写；",
                        primary_key=True,
                        serialize=False,
                        verbose_name="Chain ID",
                    ),
                ),
                ("name", models.CharField(max_length=32, unique=True, verbose_name="名称")),
                (
                    "currency_symbol",
                    models.CharField(help_text="如：ETH、BNB、MATIC 等；", max_length=64, unique=True, verbose_name="主币名"),
                ),
                ("is_poa", models.BooleanField(blank=True, editable=False, verbose_name="是否为 POA 网络")),
                ("endpoint_uri", models.CharField(max_length=256, unique=True, verbose_name="HTTP RPC 节点地址")),
                (
                    "block_confirmations_count",
                    models.PositiveSmallIntegerField(
                        default=18,
                        help_text="交易的确认数越多，则该交易在区块链中埋的越深，就越不容易被篡改；<br/>高于此确认数，系统将认定此交易被区块链最终接受；<br/>数值参考：<br/>ETH: 12; BSC: 15; Others: 16；",
                        verbose_name="区块确认数量",
                    ),
                ),
                ("active", models.BooleanField(default=True, verbose_name="启用")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="创建时间")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="更新时间")),
            ],
            options={
                "verbose_name": "网络",
                "verbose_name_plural": "网络",
            },
        ),
        migrations.CreateModel(
            name="PlatformTransaction",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nonce", models.PositiveIntegerField(verbose_name="Nonce")),
                ("to", common.fields.ChecksumAddressField(db_index=True, max_length=42, verbose_name="To")),
                ("value", models.DecimalField(decimal_places=0, default=0, max_digits=36, verbose_name="Value")),
                ("data", models.TextField(blank=True, null=True, verbose_name="Data")),
                ("gas", models.PositiveIntegerField(default=160000, verbose_name="Gas")),
                (
                    "hash",
                    common.fields.HexStr64Field(
                        blank=True, db_index=True, max_length=66, null=True, unique=True, verbose_name="哈希"
                    ),
                ),
                ("transacted_at", models.DateTimeField(blank=True, null=True, verbose_name="交易提交时间")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="创建时间")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="更新时间")),
            ],
            options={
                "verbose_name": "发送交易",
                "verbose_name_plural": "发送交易",
                "ordering": ("created_at",),
            },
        ),
        migrations.CreateModel(
            name="Transaction",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("hash", common.fields.HexStr64Field(db_index=True, max_length=66, unique=True, verbose_name="哈希")),
                ("transaction_index", models.PositiveSmallIntegerField()),
                ("metadata", models.JSONField()),
                ("receipt", models.JSONField()),
                (
                    "type",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("paying", "Paying"),
                            ("depositing", "Depositing"),
                            ("withdrawal", "Withdrawal"),
                            ("funding", "Funding"),
                            ("gas_recharging", "GasRecharging"),
                            ("d_gathering", "DepositGathering"),
                            ("i_gathering", "InvoiceGathering"),
                        ],
                        max_length=16,
                        null=True,
                        verbose_name="类型",
                    ),
                ),
            ],
            options={
                "verbose_name": "交易",
                "verbose_name_plural": "交易",
                "ordering": ("block", "transaction_index"),
            },
        ),
        migrations.CreateModel(
            name="Block",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("hash", common.fields.HexStr64Field(db_index=True, max_length=66, unique=True, verbose_name="哈希")),
                ("number", models.PositiveIntegerField(db_index=True)),
                ("timestamp", models.PositiveIntegerField()),
                ("confirmed", models.BooleanField(default=False)),
                (
                    "parent",
                    models.OneToOneField(
                        blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to="chains.block"
                    ),
                ),
            ],
            options={
                "verbose_name": "区块",
                "verbose_name_plural": "区块",
                "ordering": ("network", "-number"),
            },
        ),
    ]
