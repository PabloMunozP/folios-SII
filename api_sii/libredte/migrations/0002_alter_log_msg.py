# Generated by Django 4.0.2 on 2022-03-15 00:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('libredte', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='log',
            name='msg',
            field=models.CharField(max_length=100),
        ),
    ]