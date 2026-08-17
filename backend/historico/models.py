from django.db import models
from usuario.models import Usuario
from ordem_servico.models import OrdemServico
# Create your models here.

# Modelo para representar o histórico de ordens de serviço
class Historico(models.Model):
    id_historico_ordem_servico = models.BigAutoField(primary_key=True)

    usuario = models.ForeignKey(Usuario, on_delete=models.DO_NOTHING, db_column='id_usuario') # Relacionamento com o modelo Usuario

    ordem_servico = models.ForeignKey( OrdemServico, on_delete=models.CASCADE, db_column='id_ordem_servico') # Relacionamento com o modelo OrdemServico

    data_registro = models.DateTimeField() # Campo para armazenar a data e hora do registro do histórico
    desc_historico = models.CharField(max_length=255) # Campo para armazenar uma descrição do histórico

    class Meta:
        managed = False # Indica que o Django não deve gerenciar a criação da tabela no banco de dados
        #managed = True # Indica que o Django deve criar e gerenciar a tabela no banco de dados
        db_table = 'historico'

    def __str__(self):
        return f'Histórico OS #{self.ordem_servico.id_ordem_servico}'