# Generated by Django 5.0.6 on 2024-06-21 08:51

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0005_alter_player_uid"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="player",
            options={"verbose_name": "玩家", "verbose_name_plural": "玩家"},
        ),
    ]
