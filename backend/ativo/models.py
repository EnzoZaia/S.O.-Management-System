from django.db import models
from localizacao.models import Localizacao

class Ativo(models.Model):

    TIPOS_ATIVO = (('AR_CONDICIONADO', 'Ar Condicionado'), ('BEBEDOURO', 'Bebedouro'),)

    id_ativo = models.BigAutoField(primary_key=True)

    localizacao = models.ForeignKey(Localizacao, on_delete=models.DO_NOTHING, db_column='id_localizacao')

    codigo_patrimonial = models.CharField(max_length=100, null=True, blank=True)
    tipo_ativo = models.CharField(max_length=30, choices=TIPOS_ATIVO)
    marca = models.CharField(max_length=100, null=True, blank=True)
    modelo = models.CharField(max_length=100, null=True, blank=True)
    numero_serial = models.CharField(max_length=100, null=True, blank=True)
    periodicidade_preventiva_dias = models.IntegerField(default=90)
    dt_ultima_preventiva = models.DateField(null=True, blank=True)
    dt_proxima_preventiva = models.DateField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'ativo'

    def __str__(self):
        return f'{self.tipo_ativo} - {self.codigo_patrimonial}'
