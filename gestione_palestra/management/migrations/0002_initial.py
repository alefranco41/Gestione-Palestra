# Generated by Django 5.0.6 on 2024-05-25 12:31

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('management', '0001_initial'),
        ('palestra', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='grouptraining',
            name='trainer',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='palestra.trainerprofile'),
        ),
        migrations.AddField(
            model_name='durationdiscount',
            name='subscription_plan',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='management.subscriptionplan'),
        ),
    ]
