# Generated by Django 5.0.6 on 2024-06-21 03:19

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("chains", "0002_initial"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="network",
            options={"verbose_name": "网络", "verbose_name_plural": "网络"},
        ),
        migrations.AlterModelOptions(
            name="platformtransaction",
            options={"ordering": ("created_at",), "verbose_name": "发送交易", "verbose_name_plural": "发送交易"},
        ),
        migrations.AlterField(
            model_name="platformtransaction",
            name="network",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="chains.network", verbose_name="网络"
            ),
        ),
    ]
