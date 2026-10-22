from django.db import models
from django.utils import timezone

from ativo.models import Ativo, ManualAtivo
from ordem_servico.models import OrdemServico
from predio.models import Predio
from usuario.models import Usuario

STATUS_PENDENTE = 'PENDENTE'
STATUS_PROCESSANDO = 'PROCESSANDO'
STATUS_CONCLUIDO = 'CONCLUIDO'
STATUS_INDISPONIVEL = 'INDISPONIVEL'
STATUS_RESPOSTA_INVALIDA = 'RESPOSTA_INVALIDA'


class AssistenteTecnicoIA(models.Model):
    id_assistente = models.IntegerField(primary_key=True, default=1, db_column='id')
    provedor = models.CharField(max_length=100)
    modelo = models.CharField(max_length=100)
    disponivel = models.BooleanField(default=True)

    class Meta:
        managed = False
        db_table = 'assistente_tecnico_ia'


class ConsultaAssistenteIA(models.Model):
    id_consulta = models.AutoField(primary_key=True, db_column='id')
    tecnico = models.ForeignKey(Usuario, on_delete=models.DO_NOTHING, db_column='tecnico_id', related_name='consultas_ia')
    ordem_servico = models.ForeignKey(OrdemServico, on_delete=models.CASCADE, db_column='ordem_servico_id', related_name='consultas_ia')
    ativo = models.ForeignKey(Ativo, on_delete=models.DO_NOTHING, db_column='ativo_id', related_name='consultas_ia')
    manual = models.ForeignKey(ManualAtivo, on_delete=models.DO_NOTHING, null=True, blank=True, db_column='manual_id', related_name='consultas_ia')
    provedor_ia = models.CharField(max_length=60, null=True, blank=True)
    modelo_ia = models.CharField(max_length=60, null=True, blank=True)
    pergunta = models.TextField()
    resposta = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=20, default=STATUS_PENDENTE)
    dt_consulta = models.DateTimeField(default=timezone.now, db_column='data_consulta')

    class Meta:
        managed = False
        db_table = 'consulta_assistente_ia'


class IndicadorGerencial(models.Model):
    id_indicador = models.AutoField(primary_key=True, db_column='id')
    gerente = models.ForeignKey(Usuario, on_delete=models.DO_NOTHING, db_column='gerente_id', related_name='indicadores_gerenciais')
    predio = models.ForeignKey(Predio, on_delete=models.DO_NOTHING, null=True, blank=True, db_column='predio_id', related_name='+')
    tipo_ativo = models.CharField(max_length=30, null=True, blank=True)
    tipo = models.CharField(max_length=40)
    valor = models.DecimalField(max_digits=14, decimal_places=4)
    dt_inicio_periodo = models.DateField(db_column='data_inicio_periodo')
    dt_fim_periodo = models.DateField(db_column='data_fim_periodo')
    dt_calculo = models.DateTimeField(default=timezone.now, db_column='data_calculo')

    class Meta:
        managed = False
        db_table = 'indicador_gerencial'


class InsightGerencial(models.Model):
    id_insight = models.AutoField(primary_key=True, db_column='id')
    gerente = models.ForeignKey(Usuario, on_delete=models.DO_NOTHING, db_column='gerente_id', related_name='insights_gerenciais')
    predio = models.ForeignKey(Predio, on_delete=models.DO_NOTHING, null=True, blank=True, db_column='predio_id', related_name='+')
    dt_inicio_periodo = models.DateField(db_column='data_inicio_periodo')
    dt_fim_periodo = models.DateField(db_column='data_fim_periodo')
    provedor_ia = models.CharField(max_length=60, null=True, blank=True)
    modelo_ia = models.CharField(max_length=60, null=True, blank=True)
    conteudo = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=20, default=STATUS_PENDENTE)
    dt_geracao = models.DateTimeField(default=timezone.now, db_column='data_geracao')
    indicadores = models.ManyToManyField(IndicadorGerencial, through='InsightIndicador', related_name='insights')

    class Meta:
        managed = False
        db_table = 'insight_gerencial'


class InsightIndicador(models.Model):
    pk = models.CompositePrimaryKey('insight_id', 'indicador_id')
    insight = models.ForeignKey(InsightGerencial, on_delete=models.CASCADE, db_column='insight_id')
    indicador = models.ForeignKey(IndicadorGerencial, on_delete=models.DO_NOTHING, db_column='indicador_id')

    class Meta:
        managed = False
        db_table = 'insight_indicador'
