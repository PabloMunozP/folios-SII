# Generated by Django 4.0.2 on 2022-02-24 20:57

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0005_rename_state_cliente_estado'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Company',
        ),
    ]
