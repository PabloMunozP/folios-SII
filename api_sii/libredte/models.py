from django.db import models

# Create your models here.
class ClienteDTE(models.Model):
    name = models.CharField(max_length=60)
    rut = models.CharField(max_length=10,unique=True)
    razon_social = models.CharField(max_length=60)
    certificate = models.FileField(upload_to='api_sii/data/certificados/clientesDTE')
    certificate_pass = models.CharField(max_length=60)
    estado=models.BooleanField(default=True, name='Estado')

    def __str__(self):
        return self.name


class LogDTE(models.Model):
    date = models.DateField(auto_now_add=True)
    user =models.CharField(max_length=25)
    msg =models.CharField(max_length=100)
    service = models.CharField(max_length=25)