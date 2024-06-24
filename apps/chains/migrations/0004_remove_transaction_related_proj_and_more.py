# Generated by Django 5.0.6 on 2024-06-24 03:43

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("chains", "0003_alter_network_options_and_more"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="transaction",
            name="related_proj",
        ),
        migrations.AlterField(
            model_name="network",
            name="chain_id",
            field=models.PositiveIntegerField(
                blank=True, help_text="自动检测Chain ID，无需填写；", unique=True, verbose_name="Chain ID"
            ),
        ),
    ]
