# Generated by Django 4.0.2 on 2022-02-04 22:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0002_alter_company_certificate_delete_certificate'),
    ]

    operations = [
        migrations.AlterField(
            model_name='company',
            name='certificate',
            field=models.FileField(upload_to='api_sii/data/certificados/'),
        ),
    ]
