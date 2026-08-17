from django.db import models
from predio.models import Predio

# Create your models here.
# Modelo para representar a localização de um prédio, com um campo de descrição e um relacionamento com o modelo Predio. A tabela correspondente no banco de dados é 'localizacao', e o Django não gerencia a criação dessa tabela (managed = False).
class Localizacao(models.Model):
    id_localizacao = models.BigAutoField(primary_key=True)

    predio = models.ForeignKey(Predio, on_delete=models.DO_NOTHING, db_column='id_predio') # Relacionamento com o modelo Predio
    desc_localizacao = models.CharField(max_length=150)

    class Meta:
        managed = False # Indica que o Django não deve gerenciar a criação da tabela no banco de dados
        #managed = True # Indica que o Django deve criar e gerenciar a tabela no banco de dados
        db_table = 'localizacao'

    def __str__(self):
        return self.desc_localizacao