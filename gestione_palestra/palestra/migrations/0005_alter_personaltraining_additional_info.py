# Generated by Django 5.0.6 on 2024-05-27 14:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('palestra', '0004_alter_trainerprofile_date_of_birth'),
    ]

    operations = [
        migrations.AlterField(
            model_name='personaltraining',
            name='additional_info',
            field=models.TextField(blank=True, max_length=500),
        ),
    ]
