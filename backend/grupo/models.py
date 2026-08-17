from django.db import models

# Create your models here.

# Modelo para a tabela "grupo"
class Grupo(models.Model):
    # Campos da tabela "grupo"
    id_grupo = models.BigAutoField(primary_key=True)
    desc_grupo = models.CharField(max_length=150)
    desc_permissao = models.CharField(max_length=150, null=True, blank=True)

    # Configurações adicionais do modelo
    class Meta:
        managed = False # Indica que o Django não deve criar ou modificar a tabela no banco de dados
        #managed = True # Indica que o Django deve criar e gerenciar a tabela no banco de dados
        db_table = 'grupo'

    # Método para representar o objeto como uma string
    def __str__(self):
        return self.desc_grupo