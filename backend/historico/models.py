from django.db import models
from django.utils import timezone

from usuario.models import Usuario
from ordem_servico.models import OrdemServico
from ordem_servico.constantes import EVENTO_ATRIBUICAO

class Historico(models.Model):
    id_historico_ordem_servico = models.AutoField(primary_key=True, db_column='id')

    usuario = models.ForeignKey(Usuario, on_delete=models.DO_NOTHING, db_column='usuario_id', null=True, blank=True)

    ordem_servico = models.ForeignKey( OrdemServico, on_delete=models.CASCADE, db_column='ordem_servico_id')

    tecnico = models.ForeignKey(Usuario, on_delete=models.DO_NOTHING, db_column='tecnico_id', null=True, blank=True, related_name='atribuicoes_recebidas')

    data_registro = models.DateTimeField(default=timezone.now)
    desc_historico = models.TextField(null=True, blank=True, db_column='descricao')
    status_anterior = models.CharField(max_length=30, null=True, blank=True)
    status_novo = models.CharField(max_length=30, null=True, blank=True)
    tipo_evento = models.CharField(max_length=30, null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'historico'
        constraints = [
            models.CheckConstraint(
                condition=models.Q(tipo_evento=EVENTO_ATRIBUICAO, tecnico__isnull=False)
                | (models.Q(tecnico__isnull=True) & (~models.Q(tipo_evento=EVENTO_ATRIBUICAO) | models.Q(tipo_evento__isnull=True))),
                name='tecnico_somente_na_atribuicao',
            ),
        ]

    def __str__(self):
        return f'Histórico OS #{self.ordem_servico_id}'
