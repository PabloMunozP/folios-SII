# Generated by Django 4.0.3 on 2022-03-31 18:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('libredte', '0005_alter_clientedte_certificate'),
    ]

    operations = [
        migrations.AlterField(
            model_name='clientedte',
            name='certificate',
            field=models.FileField(upload_to='api_sii/data/certificados/clientsDTE'),
        ),
    ]
