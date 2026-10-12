from django.db import models
from localizacao.models import Localizacao

class Ativo(models.Model):

    TIPOS_ATIVO = (('AR_CONDICIONADO', 'Ar Condicionado'), ('BEBEDOURO', 'Bebedouro'),)

    id_ativo = models.AutoField(primary_key=True, db_column='id')

    localizacao = models.ForeignKey(Localizacao, on_delete=models.DO_NOTHING, db_column='localizacao_id')

    codigo_patrimonial = models.CharField(max_length=50, unique=True)
    tipo_ativo = models.CharField(max_length=30, choices=TIPOS_ATIVO)
    marca = models.CharField(max_length=100, null=True, blank=True)
    modelo = models.CharField(max_length=100, null=True, blank=True)
    numero_serial = models.CharField(max_length=100, null=True, blank=True)
    periodicidade_preventiva_dias = models.IntegerField(default=90)
    dt_ultima_preventiva = models.DateField(null=True, blank=True, db_column='data_ultima_preventiva')
    dt_proxima_preventiva = models.DateField(null=True, blank=True, db_column='data_proxima_preventiva')

    class Meta:
        managed = False
        db_table = 'ativo'
        constraints = [
            models.CheckConstraint(condition=models.Q(periodicidade_preventiva_dias__gt=0), name='ativo_periodicidade_preventiva_dias_check'),
        ]

    def __str__(self):
        return f'{self.tipo_ativo} - {self.codigo_patrimonial}'
