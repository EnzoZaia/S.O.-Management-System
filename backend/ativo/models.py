from django.db import models
from localizacao.models import Localizacao

# Create your models here.
# O modelo Ativo representa um ativo físico, como um ar condicionado ou bebedouro, com informações sobre sua localização, código patrimonial, tipo, marca, modelo, número de série, periodicidade de manutenção preventiva e datas da última e próxima manutenção preventiva. Ele inclui métodos para criar e atualizar instâncias do ativo, garantindo que a data da próxima manutenção preventiva seja calculada corretamente com base na data da última manutenção e na periodicidade.
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
        #managed = True # Indica que o Django deve criar e gerenciar a tabela no banco de dados
        db_table = 'ativo'

    def __str__(self):
        return f'{self.tipo_ativo} - {self.codigo_patrimonial}'