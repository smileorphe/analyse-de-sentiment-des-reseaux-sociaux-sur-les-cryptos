# Generated by Django 5.2 on 2025-04-17 12:14

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('crypto_sentiment', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='socialmediapost',
            name='collected_at',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]
