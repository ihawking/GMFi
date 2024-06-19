# Generated by Django 5.0.1 on 2024-02-20 09:20

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("deposits", "0001_initial"),
        ("users", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="deposit",
            name="user",
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="users.user", verbose_name="用户"),
        ),
    ]