from django.db import models
from django.utils import timezone

from ordem_servico.models import OrdemServico
from usuario.models import Usuario


class OsParticipante(models.Model):
    id_os_participante = models.BigAutoField(primary_key=True, db_column='id')

    ordem_servico = models.ForeignKey(OrdemServico, on_delete=models.CASCADE, db_column='ordem_servico_id', related_name='participantes')

    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, db_column='usuario_id', related_name='participacoes')

    dt_vinculo = models.DateTimeField(default=timezone.now, db_column='data_vinculo')

    class Meta:
        managed = False
        db_table = 'os_participante'
        unique_together = (('ordem_servico', 'usuario'),)

    def __str__(self):
        return f'{self.usuario} presenciou OS #{self.ordem_servico_id}'
