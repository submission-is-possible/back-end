# Generated by Django 5.1.3 on 2024-11-30 16:32

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('conference', '0002_rename_created_by_conference_admin_id'),
        ('papers', '0001_initial'),
        ('users', '0002_user_last_login'),
    ]

    operations = [
        migrations.CreateModel(
            name='PaperReviewAssignment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('assigned', 'Assigned'), ('reviewed', 'Reviewed'), ('approved', 'Approved')], default='assigned', max_length=20)),
                ('conference', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='review_assignments', to='conference.conference')),
                ('paper', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='review_assignments', to='papers.paper')),
                ('reviewer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='assigned_papers', to='users.user')),
            ],
        ),
    ]
