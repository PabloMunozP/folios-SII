# Generated by Django 4.0.2 on 2022-03-18 00:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0010_alter_errors_msg_alter_log_msg'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cliente',
            name='certificate',
            field=models.FileField(upload_to='api/data/certificados/clients'),
        ),
    ]
