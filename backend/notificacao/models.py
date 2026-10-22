from django.db import models
from django.utils import timezone

from ordem_servico.models import OrdemServico
from usuario.models import Usuario


class Notificacao(models.Model):
    id_notificacao = models.BigAutoField(primary_key=True, db_column='id')

    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, db_column='usuario_id', related_name='notificacoes')

    ordem_servico = models.ForeignKey(OrdemServico, on_delete=models.CASCADE, db_column='ordem_servico_id', null=True, blank=True, related_name='notificacoes')

    tipo = models.CharField(max_length=40)
    titulo = models.CharField(max_length=150)
    mensagem = models.TextField()
    lida = models.BooleanField(default=False)
    dt_criacao = models.DateTimeField(default=timezone.now, db_column='data_criacao')
    dt_leitura = models.DateTimeField(null=True, blank=True, db_column='data_leitura')

    class Meta:
        managed = False
        db_table = 'notificacao'

    def __str__(self):
        return f'{self.tipo} para {self.usuario_id}'
