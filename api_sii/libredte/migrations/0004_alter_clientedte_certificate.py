# Generated by Django 4.0.2 on 2022-03-18 00:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('libredte', '0003_rename_cliente_clientedte_rename_log_logdte'),
    ]

    operations = [
        migrations.AlterField(
            model_name='clientedte',
            name='certificate',
            field=models.FileField(upload_to='api/data/certificados/clientsDTE'),
        ),
    ]
