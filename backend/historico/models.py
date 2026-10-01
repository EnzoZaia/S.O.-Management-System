from django.db import models
from usuario.models import Usuario
from ordem_servico.models import OrdemServico

class Historico(models.Model):
    id_historico_ordem_servico = models.BigAutoField(primary_key=True)

    usuario = models.ForeignKey(Usuario, on_delete=models.DO_NOTHING, db_column='id_usuario')

    ordem_servico = models.ForeignKey( OrdemServico, on_delete=models.CASCADE, db_column='id_ordem_servico')

    data_registro = models.DateTimeField()
    desc_historico = models.CharField(max_length=255)

    class Meta:
        managed = False
        db_table = 'historico'

    def __str__(self):
        return f'Histórico OS #{self.ordem_servico.id_ordem_servico}'
