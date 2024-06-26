# Generated by Django 5.0.6 on 2024-05-25 12:31

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='DurationDiscount',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('duration', models.IntegerField(choices=[(1, '1 Month'), (3, '3 Months'), (6, '6 Months'), (12, '12 Months')])),
                ('discount_percentage', models.DecimalField(decimal_places=2, default=0, max_digits=5)),
            ],
        ),
        migrations.CreateModel(
            name='FitnessGoal',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='GroupTraining',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('day', models.CharField(choices=[('Monday', 'Monday'), ('Tuesday', 'Tuesday'), ('Wednesday', 'Wednesday'), ('Thursday', 'Thursday'), ('Friday', 'Friday'), ('Saturday', 'Saturday'), ('Sunday', 'Sunday')], max_length=10)),
                ('start_hour', models.PositiveSmallIntegerField(choices=[(9, '9:00'), (10, '10:00'), (11, '11:00'), (12, '12:00'), (13, '13:00'), (14, '14:00'), (15, '15:00'), (16, '16:00'), (17, '17:00'), (18, '18:00')])),
                ('duration', models.PositiveIntegerField()),
                ('max_participants', models.PositiveIntegerField()),
                ('total_partecipants', models.PositiveIntegerField(default=0)),
                ('title', models.TextField()),
                ('image', models.ImageField(blank=True, null=True, upload_to='group-classes/')),
            ],
        ),
        migrations.CreateModel(
            name='SubscriptionPlan',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('plan_type', models.CharField(choices=[('GROUP', 'Group Classes Only'), ('WEIGHTS', 'Gym Access Only'), ('FULL', 'Group Classes + Gym Access')], max_length=10)),
                ('monthly_price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('age_discount', models.DecimalField(decimal_places=2, default=0, max_digits=5)),
            ],
        ),
    ]
