# Generated by Django 5.0.6 on 2024-05-30 07:48

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('management', '0004_alter_grouptraining_title'),
        ('palestra', '0006_alter_grouptrainingreview_additional_info_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='CompletedGroupTrainingReservation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('completed_date', models.DateField(auto_now_add=True)),
                ('group_class', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='management.grouptraining')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AlterField(
            model_name='grouptrainingreview',
            name='event',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='palestra.completedgrouptrainingreservation'),
        ),
        migrations.CreateModel(
            name='CompletedPersonalTraining',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('day', models.CharField(choices=[('Monday', 'Monday'), ('Tuesday', 'Tuesday'), ('Wednesday', 'Wednesday'), ('Thursday', 'Thursday'), ('Friday', 'Friday'), ('Saturday', 'Saturday'), ('Sunday', 'Sunday')], max_length=10)),
                ('start_hour', models.PositiveSmallIntegerField(choices=[(9, '9:00'), (10, '10:00'), (11, '11:00'), (12, '12:00'), (13, '13:00'), (14, '14:00'), (15, '15:00'), (16, '16:00'), (17, '17:00'), (18, '18:00')])),
                ('training_type', models.CharField(max_length=10)),
                ('additional_info', models.TextField(blank=True, max_length=500)),
                ('completed_date', models.DateField(auto_now_add=True)),
                ('trainer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='palestra.trainerprofile')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AlterField(
            model_name='personaltrainingreview',
            name='event',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='palestra.completedpersonaltraining'),
        ),
    ]