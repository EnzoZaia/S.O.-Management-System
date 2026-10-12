from django.db import models
from django.db.models import Case, Count, IntegerField, OuterRef, Q, Subquery, Value, When
from django.db.models.functions import Coalesce

from localizacao.models import Localizacao
from usuario.models import Usuario
from ativo.models import Ativo
from ordem_servico.constantes import EM_TRIAGEM, EVENTO_ATRIBUICAO, PRIORIDADE_NORMAL, TIPO_CORRETIVA


def _atribuicoes(ordem_servico_ref):
    from historico.models import Historico

    return Historico.objects.filter(ordem_servico=ordem_servico_ref, tipo_evento=EVENTO_ATRIBUICAO).order_by('-data_registro', '-id_historico_ordem_servico')


class OrdemServicoQuerySet(models.QuerySet):
    def com_responsaveis(self):
        atribuicao = _atribuicoes(OuterRef('pk'))
        return self.annotate(
            tecnico_atual_id=Subquery(atribuicao.values('tecnico_id')[:1]),
            tecnico_atual_nome=Subquery(atribuicao.values('tecnico__nome')[:1]),
            gestor_atual_id=Subquery(atribuicao.values('usuario_id')[:1]),
            gestor_atual_nome=Subquery(atribuicao.values('usuario__nome')[:1]),
        )

    def com_total_afetados(self):
        from os_participante.models import OsParticipante

        participantes = (
            OsParticipante.objects.filter(ordem_servico=OuterRef('pk'))
            .filter(Q(ordem_servico__solicitante__isnull=True) | ~Q(usuario_id=OuterRef('solicitante_id')))
            .order_by()
            .values('ordem_servico')
            .annotate(total=Count('pk'))
            .values('total')[:1]
        )
        return self.annotate(
            total_afetados_anotado=Coalesce(Subquery(participantes, output_field=IntegerField()), Value(0))
            + Case(When(solicitante__isnull=False, then=Value(1)), default=Value(0), output_field=IntegerField()),
        )


class OrdemServico(models.Model):
    id_ordem_servico = models.AutoField(primary_key=True, db_column='id')

    id_solicitacao = models.IntegerField(null=True, blank=True, unique=True, db_column='solicitacao_id')

    localizacao = models.ForeignKey(Localizacao, on_delete=models.DO_NOTHING, db_column='localizacao_id')

    solicitante = models.ForeignKey(Usuario, on_delete=models.DO_NOTHING, db_column='solicitante_usuario_id', related_name='ordens_abertas', null=True, blank=True)

    ativo = models.ForeignKey(Ativo, on_delete=models.DO_NOTHING, db_column='ativo_id', null=True, blank=True)

    tipo_manutencao = models.CharField(max_length=30, default=TIPO_CORRETIVA)
    categoria_manutencao = models.CharField(max_length=50, null=True, blank=True)
    prioridade_urgencia = models.CharField(max_length=20, default=PRIORIDADE_NORMAL, db_column='prioridade')
    status_ordem_servico = models.CharField(max_length=30, default=EM_TRIAGEM, db_column='status')
    descricao_servico = models.TextField()
    causa_raiz = models.TextField(null=True, blank=True)
    dt_abertura = models.DateTimeField(db_column='data_abertura')
    dt_conclusao = models.DateTimeField(null=True, blank=True, db_column='data_conclusao')

    objects = OrdemServicoQuerySet.as_manager()

    class Meta:
        managed = False
        db_table = 'ordem_servico'

    def __str__(self):
        return f'OS #{self.id_ordem_servico}'

    def _carregar_responsaveis(self):
        if hasattr(self, 'tecnico_atual_id'):
            return
        atribuicao = None
        if self.pk:
            atribuicao = _atribuicoes(self.pk).values('tecnico_id', 'tecnico__nome', 'usuario_id', 'usuario__nome').first()
        self.tecnico_atual_id = atribuicao['tecnico_id'] if atribuicao else None
        self.tecnico_atual_nome = atribuicao['tecnico__nome'] if atribuicao else None
        self.gestor_atual_id = atribuicao['usuario_id'] if atribuicao else None
        self.gestor_atual_nome = atribuicao['usuario__nome'] if atribuicao else None

    def definir_responsaveis(self, tecnico, gestor):
        self.tecnico_atual_id = tecnico.pk if tecnico else None
        self.tecnico_atual_nome = tecnico.nome if tecnico else None
        self.gestor_atual_id = gestor.pk if gestor else None
        self.gestor_atual_nome = gestor.nome if gestor else None

    @property
    def tecnico_id(self):
        self._carregar_responsaveis()
        return self.tecnico_atual_id

    @property
    def tecnico_nome(self):
        self._carregar_responsaveis()
        return self.tecnico_atual_nome

    @property
    def tecnico(self):
        return Usuario.objects.filter(pk=self.tecnico_id).first() if self.tecnico_id else None

    @property
    def gestor_id(self):
        self._carregar_responsaveis()
        return self.gestor_atual_id

    @property
    def gestor_nome(self):
        self._carregar_responsaveis()
        return self.gestor_atual_nome

    @property
    def total_afetados(self):
        if hasattr(self, 'total_afetados_anotado'):
            return self.total_afetados_anotado
        if not self.pk:
            return 1 if self.solicitante_id else 0
        from os_participante.models import OsParticipante

        participantes = OsParticipante.objects.filter(ordem_servico_id=self.pk)
        if self.solicitante_id:
            participantes = participantes.exclude(usuario_id=self.solicitante_id)
        return participantes.count() + (1 if self.solicitante_id else 0)

    @property
    def gestor(self):
        return Usuario.objects.filter(pk=self.gestor_id).first() if self.gestor_id else None
