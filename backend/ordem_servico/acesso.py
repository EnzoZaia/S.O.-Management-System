from abc import ABC, abstractmethod
from datetime import timedelta

from django.db.models import Avg, Count, F, Q, QuerySet
from django.utils import timezone

from ordem_servico.constantes import (
    ABERTA,
    AGUARDANDO_MATERIAL,
    AGUARDANDO_TERCEIRO,
    AGUARDANDO_VALIDACAO,
    APROVADA,
    EM_EXECUCAO,
    REPROVADA,
    STATUS_FINALIZADOS,
    STATUS_VALIDOS,
    TIPO_PREVENTIVA,
    status_para_api,
)
from ordem_servico.models import OrdemServico
from utils.permissions import usuario_tem_grupo


def _filtro_solicitante_ou_participante(usuario) -> Q:
    from os_participante.models import OsParticipante

    ids_presenciadas = OsParticipante.objects.filter(usuario=usuario).values('ordem_servico_id')
    return Q(solicitante=usuario) | Q(id_ordem_servico__in=ids_presenciadas)


class EscopoConsultaOS(ABC):
    """Produto abstrato: quais OS um perfil pode listar/acessar."""

    @abstractmethod
    def filtrar(self, usuario) -> QuerySet:
        ...


class RegraDashboard(ABC):
    """Produto abstrato: como calcular os indicadores do dashboard para um perfil."""

    @abstractmethod
    def calcular_indicadores(self, usuario, periodo: str) -> dict:
        ...


class EscopoConsultaOSGerente(EscopoConsultaOS):
    def filtrar(self, usuario) -> QuerySet:
        return OrdemServico.objects.com_responsaveis().order_by('-dt_abertura')


class EscopoConsultaOSGestor(EscopoConsultaOS):
    def filtrar(self, usuario) -> QuerySet:
        return OrdemServico.objects.com_responsaveis().filter(
            Q(gestor_atual_id=usuario.pk) | Q(status_ordem_servico=ABERTA)
        ).order_by('-dt_abertura')


class EscopoConsultaOSTecnico(EscopoConsultaOS):
    def filtrar(self, usuario) -> QuerySet:
        return OrdemServico.objects.com_responsaveis().filter(tecnico_atual_id=usuario.pk).order_by('-dt_abertura')


class EscopoConsultaOSSolicitante(EscopoConsultaOS):
    def filtrar(self, usuario) -> QuerySet:
        return OrdemServico.objects.com_responsaveis().filter(_filtro_solicitante_ou_participante(usuario)).order_by('-dt_abertura')


class _RegraDashboardBase(RegraDashboard):
    """Cálculo de indicadores comum a todos os perfis; cada subclasse só define a base de OS."""

    def _query_base(self, usuario) -> QuerySet:
        raise NotImplementedError

    def calcular_indicadores(self, usuario, periodo: str) -> dict:
        base_query = self._query_base(usuario)
        agora = timezone.now()

        if periodo == 'mes_atual':
            base_query = base_query.filter(dt_abertura__year=agora.year, dt_abertura__month=agora.month)
        elif periodo == 'mes_passado':
            mes_passado = agora.month - 1 if agora.month > 1 else 12
            ano_passado = agora.year if agora.month > 1 else agora.year - 1
            base_query = base_query.filter(dt_abertura__year=ano_passado, dt_abertura__month=mes_passado)
        elif periodo == 'ano':
            base_query = base_query.filter(dt_abertura__year=agora.year)
        else:
            limite_data = agora - timedelta(days=30)
            base_query = base_query.filter(dt_abertura__gte=limite_data)

        total_ordens = base_query.count()
        status_counts = base_query.values('status_ordem_servico').annotate(total=Count('id_ordem_servico'))

        contagens = {status_os: 0 for status_os in STATUS_VALIDOS}
        for item in status_counts:
            if item['status_ordem_servico'] in contagens:
                contagens[item['status_ordem_servico']] = item['total']

        tipo_counts = base_query.values('tipo_manutencao').annotate(total=Count('id_ordem_servico'))
        tipos_dict = {'preventiva': 0, 'corretiva': 0}
        for t in tipo_counts:
            if t['tipo_manutencao'] == TIPO_PREVENTIVA:
                tipos_dict['preventiva'] += t['total']
            else:
                tipos_dict['corretiva'] += t['total']

        ordens_finalizadas = base_query.filter(dt_conclusao__isnull=False, status_ordem_servico__in=STATUS_FINALIZADOS)
        tempo_medio = "0d"
        if ordens_finalizadas.exists():
            try:
                dados_tempo = ordens_finalizadas.annotate(duracao=F('dt_conclusao') - F('dt_abertura')).aggregate(media_duracao=Avg('duracao'))
                if dados_tempo['media_duracao']:
                    duracao = dados_tempo['media_duracao']
                    dias = duracao.days + (duracao.seconds / 86400)
                    tempo_medio = f"{dias:.1f}d"
            except Exception:
                pass

        linhas_os = list(base_query.values_list('id_ordem_servico', 'tecnico_atual_id', 'tecnico_atual_nome', 'status_ordem_servico'))
        tecnico_por_os = {id_os: id_tecnico for id_os, id_tecnico, _, _ in linhas_os}
        satisfacao = self._calcular_satisfacao(base_query, tecnico_por_os)

        ranking = {}
        for _, id_tecnico, nome_tecnico, status_os in linhas_os:
            if id_tecnico is None:
                continue
            item = ranking.setdefault(id_tecnico, {'nome': nome_tecnico, 'concluidas': 0, 'total': 0})
            item['total'] += 1
            if status_os in STATUS_FINALIZADOS:
                item['concluidas'] += 1

        media_por_tecnico = satisfacao['por_tecnico']
        tecnicos_data = [
            {
                **item,
                'satisfacao_media': media_por_tecnico.get(id_tecnico, {}).get('media'),
                'total_avaliacoes': media_por_tecnico.get(id_tecnico, {}).get('total', 0),
            }
            for id_tecnico, item in sorted(ranking.items(), key=lambda par: (-par[1]['concluidas'], -par[1]['total']))[:4]
        ]

        semanas_data = []
        for i in range(5, -1, -1):
            fim_semana = agora - timedelta(weeks=i)
            inicio_semana = fim_semana - timedelta(days=7)
            qtd_semana = base_query.filter(status_ordem_servico__in=STATUS_FINALIZADOS, dt_conclusao__range=(inicio_semana, fim_semana)).count()
            semanas_data.append({'label': f'Sem {6 - i}', 'valor': qtd_semana})

        return {
            'totalOrdens': total_ordens,
            'abertas': contagens[ABERTA],
            'emExecucao': contagens[EM_EXECUCAO],
            'concluidas': sum(contagens[status_os] for status_os in STATUS_FINALIZADOS),
            'aguardandoValidacao': contagens[AGUARDANDO_VALIDACAO],
            'tempo_medio': tempo_medio,
            'statusDetalhados': {status_para_api(status_os): total for status_os, total in contagens.items()},
            'tipo_manutencao': tipos_dict,
            'rankingTecnicos': tecnicos_data,
            'satisfacaoMedia': satisfacao['media'],
            'totalAvaliacoes': satisfacao['total'],
            'pendencias': {
                'aguardando_aprovacao': contagens[ABERTA],
                'aguardando_material': contagens[AGUARDANDO_MATERIAL],
                'aguardando_terceiro': contagens[AGUARDANDO_TERCEIRO],
                'aguardando_validacao': contagens[AGUARDANDO_VALIDACAO],
                'sem_tecnico': base_query.filter(tecnico_atual_id__isnull=True, status_ordem_servico=APROVADA).count()
            },
            'semanas': semanas_data,
        }

    @staticmethod
    def _calcular_satisfacao(base_query: QuerySet, tecnico_por_os: dict) -> dict:
        from validacao.models import ValidacaoAtendimento

        avaliacoes = ValidacaoAtendimento.objects.filter(ordem_servico__in=base_query.values('id_ordem_servico'), nota__isnull=False)
        geral = avaliacoes.aggregate(media=Avg('nota'), total=Count('id_validacao'))

        notas_por_tecnico = {}
        for id_os, nota in avaliacoes.values_list('ordem_servico_id', 'nota'):
            id_tecnico = tecnico_por_os.get(id_os)
            if id_tecnico is not None:
                notas_por_tecnico.setdefault(id_tecnico, []).append(nota)

        por_tecnico = {
            id_tecnico: {'media': round(sum(notas) / len(notas), 2), 'total': len(notas)}
            for id_tecnico, notas in notas_por_tecnico.items()
        }

        return {
            'media': round(float(geral['media']), 2) if geral['media'] is not None else None,
            'total': geral['total'],
            'por_tecnico': por_tecnico,
        }


class RegraDashboardGerente(_RegraDashboardBase):
    def _query_base(self, usuario) -> QuerySet:
        return OrdemServico.objects.com_responsaveis()


class RegraDashboardGestor(_RegraDashboardBase):
    def _query_base(self, usuario) -> QuerySet:
        return OrdemServico.objects.com_responsaveis().filter(
            Q(gestor_atual_id=usuario.pk) | Q(status_ordem_servico=ABERTA) | Q(status_ordem_servico=REPROVADA)
        )


class RegraDashboardTecnico(_RegraDashboardBase):
    def _query_base(self, usuario) -> QuerySet:
        return OrdemServico.objects.com_responsaveis().filter(tecnico_atual_id=usuario.pk)


class RegraDashboardSolicitante(_RegraDashboardBase):
    def _query_base(self, usuario) -> QuerySet:
        return OrdemServico.objects.com_responsaveis().filter(_filtro_solicitante_ou_participante(usuario))


class PerfilAcessoFactory(ABC):
    """Fábrica abstrata: cada perfil produz o par escopo de consulta + regra de dashboard compatível entre si."""

    @abstractmethod
    def criar_escopo_consulta(self) -> EscopoConsultaOS:
        ...

    @abstractmethod
    def criar_regra_dashboard(self) -> RegraDashboard:
        ...


class GerenteAcessoFactory(PerfilAcessoFactory):
    def criar_escopo_consulta(self) -> EscopoConsultaOS:
        return EscopoConsultaOSGerente()

    def criar_regra_dashboard(self) -> RegraDashboard:
        return RegraDashboardGerente()


class GestorAcessoFactory(PerfilAcessoFactory):
    def criar_escopo_consulta(self) -> EscopoConsultaOS:
        return EscopoConsultaOSGestor()

    def criar_regra_dashboard(self) -> RegraDashboard:
        return RegraDashboardGestor()


class TecnicoAcessoFactory(PerfilAcessoFactory):
    def criar_escopo_consulta(self) -> EscopoConsultaOS:
        return EscopoConsultaOSTecnico()

    def criar_regra_dashboard(self) -> RegraDashboard:
        return RegraDashboardTecnico()


class SolicitanteAcessoFactory(PerfilAcessoFactory):
    def criar_escopo_consulta(self) -> EscopoConsultaOS:
        return EscopoConsultaOSSolicitante()

    def criar_regra_dashboard(self) -> RegraDashboard:
        return RegraDashboardSolicitante()


def resolver_fabrica_acesso(usuario) -> PerfilAcessoFactory:
    """Resolve a fábrica pelo grupo do usuário, na ordem GERENTE > GESTOR > TECNICO > SOLICITANTE (default)."""
    if usuario_tem_grupo(usuario, "GERENTE"):
        return GerenteAcessoFactory()
    if usuario_tem_grupo(usuario, "GESTOR"):
        return GestorAcessoFactory()
    if usuario_tem_grupo(usuario, "TECNICO"):
        return TecnicoAcessoFactory()
    return SolicitanteAcessoFactory()
