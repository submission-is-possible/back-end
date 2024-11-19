# Generated by Django 5.1.3 on 2024-11-17 13:39

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('conference', '0002_rename_created_by_conference_admin_id'),
        ('notifications', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='notification',
            old_name='creation_date',
            new_name='created_at',
        ),
        migrations.RenameField(
            model_name='notification',
            old_name='id_user2',
            new_name='user_receiver',
        ),
        migrations.RenameField(
            model_name='notification',
            old_name='id_user1',
            new_name='user_sender',
        ),
        migrations.RemoveField(
            model_name='notification',
            name='description',
        ),
        migrations.RemoveField(
            model_name='notification',
            name='read',
        ),
        migrations.RemoveField(
            model_name='notification',
            name='title',
        ),
        migrations.AddField(
            model_name='notification',
            name='conference',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='notifications', to='conference.conference'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='notification',
            name='status',
            field=models.IntegerField(choices=[(-1, 'rejected'), (0, 'pending'), (1, 'accepted')], default=0),
        ),
        migrations.AlterField(
            model_name='notification',
            name='type',
            field=models.IntegerField(choices=[(0, 'author'), (1, 'reviewer')], default=0),
        ),
    ]
