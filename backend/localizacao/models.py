from django.db import models
from predio.models import Predio

class Localizacao(models.Model):
    id_localizacao = models.BigAutoField(primary_key=True)

    predio = models.ForeignKey(Predio, on_delete=models.DO_NOTHING, db_column='id_predio')
    desc_localizacao = models.CharField(max_length=150)

    class Meta:
        managed = False
        db_table = 'localizacao'

    def __str__(self):
        return self.desc_localizacao
