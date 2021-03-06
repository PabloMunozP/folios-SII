# Generated by Django 4.0.2 on 2022-03-11 18:29

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Cliente',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=60)),
                ('rut', models.CharField(max_length=10, unique=True)),
                ('razon_social', models.CharField(max_length=60)),
                ('certificate', models.FileField(upload_to='api_sii/data/certificados/clients')),
                ('certificate_pass', models.CharField(max_length=60)),
                ('Estado', models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name='Log',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(auto_now_add=True)),
                ('user', models.CharField(max_length=25)),
                ('msg', models.CharField(max_length=50)),
                ('service', models.CharField(max_length=25)),
            ],
        ),
    ]
