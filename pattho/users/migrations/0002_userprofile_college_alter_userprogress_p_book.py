# Generated by Django 5.2.3 on 2025-07-10 13:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='college',
            field=models.CharField(blank=True, choices=[('hsc', 'HSC'), ('eng', 'Engineering'), ('med', 'Medical'), ('var', 'Varsity')], max_length=20, null=True),
        ),
        migrations.AlterField(
            model_name='userprogress',
            name='p_book',
            field=models.BooleanField(default=False, help_text='Class/concept done?'),
        ),
    ]
