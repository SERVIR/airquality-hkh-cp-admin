# Generated by Django 4.1.6 on 2023-03-09 13:43

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('AqApp', '0005_alter_locationdata_pollutant'),
    ]

    operations = [
        migrations.RenameField(
            model_name='locationdata',
            old_name='Pollutant',
            new_name='pollutant',
        ),
    ]
