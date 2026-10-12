from django.db import models
from django.utils import timezone

from usuario.models import Usuario


class AuditoriaUsuario(models.Model):
    id_auditoria = models.BigAutoField(primary_key=True, db_column='id')

    usuario_alvo = models.ForeignKey(Usuario, on_delete=models.DO_NOTHING, db_column='usuario_alvo_id', related_name='auditorias_recebidas')

    autor = models.ForeignKey(Usuario, on_delete=models.DO_NOTHING, db_column='autor_usuario_id', related_name='auditorias_realizadas')

    campo = models.CharField(max_length=50)
    valor_anterior = models.CharField(max_length=255, null=True, blank=True)
    valor_novo = models.CharField(max_length=255, null=True, blank=True)
    dt_registro = models.DateTimeField(default=timezone.now, db_column='data_registro')

    class Meta:
        managed = False
        db_table = 'auditoria_usuario'

    def __str__(self):
        return f'{self.campo}: {self.valor_anterior} -> {self.valor_novo} ({self.usuario_alvo})'
