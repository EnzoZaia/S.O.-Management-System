from django.db import models
from localizacao.models import Localizacao
from usuario.models import Usuario
from ativo.models import Ativo
 # Create your models here.

# Modelo para a tabela ordem_servico
class OrdemServico(models.Model):
    id_ordem_servico = models.BigAutoField(primary_key=True)
    
    localizacao = models.ForeignKey(Localizacao, on_delete=models.DO_NOTHING, db_column='id_localizacao')

    solicitante = models.ForeignKey(Usuario, on_delete=models.DO_NOTHING, db_column='id_solicitante', related_name='ordens_abertas', null=True, blank=True)

    gestor = models.ForeignKey(Usuario, on_delete=models.DO_NOTHING, db_column='id_gestor', related_name='ordens_gerenciadas', null=True, blank=True)

    tecnico = models.ForeignKey(Usuario, on_delete=models.DO_NOTHING, db_column='id_tecnico', related_name='ordens_atribuidas', null=True, blank=True)

    ativo = models.ForeignKey(Ativo, on_delete=models.DO_NOTHING, db_column='id_ativo', null=True, blank=True) # campo para armazenar o ativo relacionado à ordem de serviço, pode ser nulo ou em branco

    tipo_manutencao = models.CharField(max_length=30, default='CORRETIVA')
    categoria_manutencao = models.CharField(max_length=50, null=True, blank=True) 
    prioridade_urgencia = models.CharField(max_length=20) # campo para armazenar a prioridade e urgência da ordem de serviço
    status_ordem_servico = models.CharField(max_length=30) # campo para armazenar o status da ordem de serviço
    dt_abertura = models.DateTimeField() # campo para armazenar a data e hora de abertura da ordem de serviço
    dt_conclusao = models.DateTimeField(null=True, blank=True) # campo para armazenar a data e hora de conclusão da ordem de serviço
    descricao_servico = models.CharField(max_length=255) # campo para armazenar a descrição do serviço da ordem de serviço

    class Meta:
        managed = False # Indica que o Django não deve gerenciar a criação da tabela no banco de dados
        #managed = True # Indica que o Django deve criar e gerenciar a tabela no banco de dados
        db_table = 'ordem_servico'

    def __str__(self):
        return f'OS #{self.id_ordem_servico}'