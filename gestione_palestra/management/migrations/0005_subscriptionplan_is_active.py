# Generated by Django 5.0.6 on 2024-06-10 07:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('management', '0004_alter_grouptraining_title'),
    ]

    operations = [
        migrations.AddField(
            model_name='subscriptionplan',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
    ]
