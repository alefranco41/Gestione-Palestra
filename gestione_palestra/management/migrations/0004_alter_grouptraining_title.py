# Generated by Django 5.0.6 on 2024-05-27 14:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('management', '0003_alter_durationdiscount_discount_percentage'),
    ]

    operations = [
        migrations.AlterField(
            model_name='grouptraining',
            name='title',
            field=models.TextField(max_length=100),
        ),
    ]
