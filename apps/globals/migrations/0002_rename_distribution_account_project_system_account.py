# Generated by Django 5.0.6 on 2024-06-30 02:55

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("globals", "0001_initial"),
    ]

    operations = [
        migrations.RenameField(
            model_name="project",
            old_name="distribution_account",
            new_name="system_account",
        ),
    ]
