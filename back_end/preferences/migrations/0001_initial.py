# Generated by Django 5.1.3 on 2024-12-03 12:54

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('papers', '0001_initial'),
        ('users', '0002_user_last_login'),
    ]

    operations = [
        migrations.CreateModel(
            name='Preference',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('preference', models.IntegerField()),
                ('paper', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='preferences', to='papers.paper')),
                ('reviewer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='preferences', to='users.user')),
            ],
        ),
    ]