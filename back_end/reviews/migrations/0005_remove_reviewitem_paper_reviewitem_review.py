# Generated by Django 5.1.3 on 2024-12-15 17:56

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reviews', '0004_reviewitem'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='reviewitem',
            name='paper',
        ),
        migrations.AddField(
            model_name='reviewitem',
            name='review',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='reviewsItem', to='reviews.review'),
            preserve_default=False,
        ),
    ]
