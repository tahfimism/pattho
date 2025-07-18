# Generated by Django 5.2.3 on 2025-07-07 03:52

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('syllabus', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='StudyRoutine',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('daily_minutes', models.PositiveIntegerField(default=120)),
                ('start_date', models.DateField(default=django.utils.timezone.now)),
                ('end_date', models.DateField()),
            ],
        ),
        migrations.CreateModel(
            name='PlannedTask',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('allocated_minutes', models.PositiveIntegerField()),
                ('completed', models.BooleanField(default=False)),
                ('topic', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='syllabus.topic')),
            ],
            options={
                'ordering': ['date'],
            },
        ),
    ]
