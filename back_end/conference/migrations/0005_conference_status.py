# Generated by Django 5.1.3 on 2024-12-06 21:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('conference', '0004_conference_automatic_assign_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='conference',
            name='status',
            field=models.CharField(choices=[('none', 'None'), ('single_blind', 'Single Blind'), ('double_blind', 'Double Blind')], default='none', max_length=20),
        ),
    ]
