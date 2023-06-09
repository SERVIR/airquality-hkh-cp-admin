# Generated by Django 4.1.6 on 2023-03-20 16:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('AqApp', '0009_alter_locationdata_options_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='locationdata',
            name='max_aqi',
            field=models.FloatField(blank=True, default=0, null=True),
        ),
        migrations.AlterField(
            model_name='locationdata',
            name='min_aqi',
            field=models.FloatField(blank=True, default=0, null=True),
        ),
    ]
