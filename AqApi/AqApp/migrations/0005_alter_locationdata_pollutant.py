# Generated by Django 4.1.6 on 2023-03-09 13:40

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('AqApp', '0004_locationdata_pollutant_locationdata_max_aqi_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='locationdata',
            name='Pollutant',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='AqApp.polluantdata'),
        ),
    ]
