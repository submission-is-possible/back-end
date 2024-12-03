# Generated by Django 5.1.2 on 2024-12-03 19:03


from django.db import migrations, models
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('conference', '0002_rename_created_by_conference_admin_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='conference',
            name='papers_deadline',
            field=models.DateTimeField(default=datetime.datetime.now),
            preserve_default=False,
        ),
    ]
