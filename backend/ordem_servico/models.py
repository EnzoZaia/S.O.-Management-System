from django.db import models
from localizacao.models import Localizacao
from usuario.models import Usuario
from ativo.models import Ativo

class OrdemServico(models.Model):
    id_ordem_servico = models.BigAutoField(primary_key=True)

    localizacao = models.ForeignKey(Localizacao, on_delete=models.DO_NOTHING, db_column='id_localizacao')

    solicitante = models.ForeignKey(Usuario, on_delete=models.DO_NOTHING, db_column='id_solicitante', related_name='ordens_abertas', null=True, blank=True)

    gestor = models.ForeignKey(Usuario, on_delete=models.DO_NOTHING, db_column='id_gestor', related_name='ordens_gerenciadas', null=True, blank=True)

    tecnico = models.ForeignKey(Usuario, on_delete=models.DO_NOTHING, db_column='id_tecnico', related_name='ordens_atribuidas', null=True, blank=True)

    ativo = models.ForeignKey(Ativo, on_delete=models.DO_NOTHING, db_column='id_ativo', null=True, blank=True)

    tipo_manutencao = models.CharField(max_length=30, default='CORRETIVA')
    categoria_manutencao = models.CharField(max_length=50, null=True, blank=True) 
    prioridade_urgencia = models.CharField(max_length=20)
    status_ordem_servico = models.CharField(max_length=30)
    dt_abertura = models.DateTimeField()
    dt_conclusao = models.DateTimeField(null=True, blank=True)
    descricao_servico = models.CharField(max_length=255)

    class Meta:
        managed = False
        db_table = 'ordem_servico'

    def __str__(self):
        return f'OS #{self.id_ordem_servico}'
