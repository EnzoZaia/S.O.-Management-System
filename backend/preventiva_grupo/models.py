from django.db import models
from django.utils import timezone

from ativo.models import Ativo
from ordem_servico.models import OrdemServico
from usuario.models import Usuario

RESULTADO_PENDENTE = 'PENDENTE'
RESULTADO_CONCLUIDO = 'CONCLUIDO'
RESULTADO_NAO_CONCLUIDO = 'NAO_CONCLUIDO'

ITEM_PENDENTE = 'PENDENTE'
ITEM_EXECUTADO = 'EXECUTADO'
ITEM_NAO_EXECUTADO = 'NAO_EXECUTADO'


class OrdemServicoAtivo(models.Model):
    id_ordem_servico_ativo = models.BigAutoField(primary_key=True, db_column='id')

    ordem_servico = models.ForeignKey(OrdemServico, on_delete=models.CASCADE, db_column='ordem_servico_id', related_name='itens_preventiva')

    ativo = models.ForeignKey(Ativo, on_delete=models.DO_NOTHING, db_column='ativo_id', related_name='itens_preventiva')

    resultado = models.CharField(max_length=20, default=RESULTADO_PENDENTE)
    motivo = models.TextField(null=True, blank=True)
    dt_resultado = models.DateTimeField(null=True, blank=True, db_column='data_resultado')
    usuario_resultado = models.ForeignKey(Usuario, on_delete=models.DO_NOTHING, null=True, blank=True, db_column='usuario_resultado_id', related_name='+')

    class Meta:
        managed = False
        db_table = 'ordem_servico_ativo'
        unique_together = (('ordem_servico', 'ativo'),)

    def __str__(self):
        return f'OS #{self.ordem_servico_id} - ativo {self.ativo_id}'


class ChecklistItemAtivo(models.Model):
    id_checklist_item = models.BigAutoField(primary_key=True, db_column='id')

    item_ordem = models.ForeignKey(OrdemServicoAtivo, on_delete=models.CASCADE, db_column='ordem_servico_ativo_id', related_name='checklist')

    codigo_item = models.IntegerField()
    descricao = models.CharField(max_length=255)
    resultado = models.CharField(max_length=20, default=ITEM_PENDENTE)
    motivo = models.TextField(null=True, blank=True)
    dt_resposta = models.DateTimeField(null=True, blank=True, db_column='data_resposta')
    usuario = models.ForeignKey(Usuario, on_delete=models.DO_NOTHING, null=True, blank=True, db_column='usuario_id', related_name='+')

    class Meta:
        managed = False
        db_table = 'checklist_item_ativo'
        unique_together = (('item_ordem', 'codigo_item'),)

    def __str__(self):
        return f'{self.codigo_item} - {self.descricao}'


class PlanoManutencaoPreventiva(models.Model):
    id_plano_manutencao = models.AutoField(primary_key=True, db_column='id')
    predio = models.ForeignKey('predio.Predio', on_delete=models.DO_NOTHING, db_column='predio_id', related_name='planos_preventiva')
    tipo_ativo = models.CharField(max_length=30)
    ciclo_dias = models.IntegerField()
    dt_criacao = models.DateTimeField(default=timezone.now, db_column='data_criacao')
    ativo_no_sistema = models.BooleanField(default=True)

    class Meta:
        managed = False
        db_table = 'plano_manutencao_preventiva'
        unique_together = (('predio', 'tipo_ativo'),)
        constraints = [
            models.CheckConstraint(condition=models.Q(ciclo_dias__gt=0), name='plano_manutencao_preventiva_ciclo_dias_check'),
        ]


class PlanoDeAcao(models.Model):
    id_plano_acao = models.AutoField(primary_key=True, db_column='id')
    plano_manutencao = models.ForeignKey(PlanoManutencaoPreventiva, on_delete=models.DO_NOTHING, null=True, blank=True, db_column='plano_manutencao_id', related_name='planos_de_acao')
    descricao = models.TextField()
    dt_criacao = models.DateTimeField(default=timezone.now, db_column='data_criacao')
    dt_conclusao = models.DateTimeField(null=True, blank=True, db_column='data_conclusao')
    status = models.CharField(max_length=20, default='PENDENTE')

    class Meta:
        managed = False
        db_table = 'plano_de_acao'


class RecursoManutencao(models.Model):
    id_recurso = models.AutoField(primary_key=True, db_column='id')
    nome = models.CharField(max_length=120)
    tipo = models.CharField(max_length=20)
    unidade_medida = models.CharField(max_length=20)

    class Meta:
        managed = False
        db_table = 'recurso_manutencao'
        unique_together = (('nome', 'tipo'),)


class PlanoAcaoRecurso(models.Model):
    pk = models.CompositePrimaryKey('plano_acao_id', 'recurso_id')
    plano_acao = models.ForeignKey(PlanoDeAcao, on_delete=models.CASCADE, db_column='plano_acao_id', related_name='recursos')
    recurso = models.ForeignKey(RecursoManutencao, on_delete=models.DO_NOTHING, db_column='recurso_id', related_name='+')
    quantidade = models.DecimalField(max_digits=12, decimal_places=3)

    class Meta:
        managed = False
        db_table = 'plano_acao_recurso'
