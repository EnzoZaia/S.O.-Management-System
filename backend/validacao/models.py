import os
import uuid

from django.db import models
from django.utils import timezone

from ordem_servico.constantes import AGUARDANDO_VALIDACAO
from ordem_servico.models import OrdemServico
from usuario.models import Usuario

RESULTADO_APROVADA = 'APROVADA'
RESULTADO_REPROVADA = 'REPROVADA'


class ValidacaoAtendimento(models.Model):
    id_validacao = models.AutoField(primary_key=True, db_column='id')

    ordem_servico = models.ForeignKey(OrdemServico, on_delete=models.CASCADE, db_column='ordem_servico_id', related_name='validacoes')

    usuario = models.ForeignKey(Usuario, on_delete=models.DO_NOTHING, db_column='usuario_id', related_name='validacoes_respondidas')

    resultado = models.CharField(max_length=20, null=True, blank=True)
    justificativa = models.TextField(null=True, blank=True)
    nota = models.SmallIntegerField(null=True, blank=True)
    comentario = models.TextField(null=True, blank=True)
    dt_validacao = models.DateTimeField(default=timezone.now, db_column='data_validacao')

    class Meta:
        managed = False
        db_table = 'validacao_atendimento'
        unique_together = (('ordem_servico', 'usuario'),)
        constraints = [
            models.CheckConstraint(condition=models.Q(nota__gte=1, nota__lte=5) | models.Q(nota__isnull=True), name='validacao_atendimento_nota_check'),
            models.CheckConstraint(condition=~models.Q(resultado=RESULTADO_REPROVADA) | models.Q(resultado__isnull=True) | models.Q(justificativa__isnull=False), name='reprovacao_exige_justificativa'),
        ]

    def __str__(self):
        return f'Validação OS #{self.ordem_servico_id} ({self.resultado})'

    @property
    def aprovada(self):
        return self.resultado == RESULTADO_APROVADA

    @classmethod
    def respostas(cls, ordem_servico):
        return (
            cls.objects.filter(ordem_servico=ordem_servico, resultado__isnull=False)
            .select_related('usuario')
            .order_by('-dt_validacao', '-id_validacao')
        )

    @classmethod
    def ultima_da_os(cls, ordem_servico):
        return cls.respostas(ordem_servico).first()

    @classmethod
    def inicio_ciclo_atual(cls, ordem_servico):
        from historico.models import Historico

        return (
            Historico.objects.filter(ordem_servico=ordem_servico, status_novo=AGUARDANDO_VALIDACAO)
            .order_by('-data_registro', '-id_historico_ordem_servico')
            .values_list('data_registro', flat=True)
            .first()
        )

    @classmethod
    def do_ciclo_atual(cls, ordem_servico):
        inicio = cls.inicio_ciclo_atual(ordem_servico)
        if inicio is None:
            return None
        return cls.respostas(ordem_servico).filter(dt_validacao__gte=inicio).first()

    @classmethod
    def avaliacao_da_os(cls, ordem_servico):
        return (
            cls.objects.filter(ordem_servico=ordem_servico, nota__isnull=False)
            .select_related('usuario')
            .order_by('-dt_validacao', '-id_validacao')
            .first()
        )


def _caminho_evidencia(instancia, nome_arquivo):
    extensao = os.path.splitext(nome_arquivo)[1].lower()
    return f'evidencias_validacao/{instancia.validacao.ordem_servico_id}/{uuid.uuid4().hex}{extensao}'


class EvidenciaValidacao(models.Model):
    id_evidencia = models.BigAutoField(primary_key=True, db_column='id')

    validacao = models.ForeignKey(ValidacaoAtendimento, on_delete=models.CASCADE, db_column='validacao_atendimento_id', related_name='evidencias')

    arquivo = models.FileField(upload_to=_caminho_evidencia, max_length=255, db_column='caminho_arquivo')
    nome_original = models.CharField(max_length=255)
    dt_upload = models.DateTimeField(default=timezone.now, db_column='data_upload')

    class Meta:
        managed = False
        db_table = 'evidencia_validacao'

    def __str__(self):
        return self.nome_original
