import os
import uuid

from django.db import models
from django.utils import timezone

from ordem_servico.models import OrdemServico
from usuario.models import Usuario

TIPO_IMAGEM = 'IMAGEM'
TIPO_VIDEO = 'VIDEO'


def _caminho_evidencia_ordem(instancia, nome_arquivo):
    extensao = os.path.splitext(nome_arquivo)[1].lower()
    return f'evidencias_ordem/{instancia.ordem_servico_id}/{uuid.uuid4().hex}{extensao}'


class EvidenciaOrdem(models.Model):
    id_evidencia_ordem = models.BigAutoField(primary_key=True, db_column='id')

    ordem_servico = models.ForeignKey(OrdemServico, on_delete=models.CASCADE, db_column='ordem_servico_id', related_name='evidencias')

    # Nulo quando a evidência vem de uma abertura anônima (aluno/funcionário sem login).
    usuario = models.ForeignKey(Usuario, on_delete=models.DO_NOTHING, db_column='usuario_id', related_name='evidencias_enviadas', null=True, blank=True)

    sequencia = models.IntegerField()
    tipo_arquivo = models.CharField(max_length=10)
    tipo_conteudo = models.CharField(max_length=60)
    arquivo = models.FileField(upload_to=_caminho_evidencia_ordem, max_length=255, db_column='caminho_arquivo')
    nome_original = models.CharField(max_length=255)
    tamanho_bytes = models.BigIntegerField()
    dt_envio = models.DateTimeField(default=timezone.now, db_column='data_envio')

    class Meta:
        managed = False
        db_table = 'evidencia_ordem'
        unique_together = (('ordem_servico', 'sequencia'),)

    def __str__(self):
        return f'Evidência {self.sequencia} da OS #{self.ordem_servico_id}'
