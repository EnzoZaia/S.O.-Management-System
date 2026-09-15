from abc import ABC, abstractmethod
from datetime import timedelta

from django.db.models import Avg, Count, F, Q, QuerySet
from django.utils import timezone

from ordem_servico.models import OrdemServico
from utils.permissions import usuario_tem_grupo


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
        return OrdemServico.objects.all().order_by('-dt_abertura')


class EscopoConsultaOSGestor(EscopoConsultaOS):
    def filtrar(self, usuario) -> QuerySet:
        return OrdemServico.objects.filter(
            Q(gestor=usuario) | Q(status_ordem_servico='ABERTA')
        ).order_by('-dt_abertura')


class EscopoConsultaOSTecnico(EscopoConsultaOS):
    def filtrar(self, usuario) -> QuerySet:
        return OrdemServico.objects.filter(tecnico=usuario).order_by('-dt_abertura')


class EscopoConsultaOSSolicitante(EscopoConsultaOS):
    def filtrar(self, usuario) -> QuerySet:
        return OrdemServico.objects.filter(solicitante=usuario).order_by('-dt_abertura')


class _RegraDashboardBase(RegraDashboard):
    """Cálculo de indicadores comum a todos os perfis; cada subclasse só define a base de OS."""

    def _query_base(self, usuario) -> QuerySet:
        raise NotImplementedError

    def calcular_indicadores(self, usuario, periodo: str) -> dict:
        from usuario.models import Usuario

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
        else:  # '30d' default
            limite_data = agora - timedelta(days=30)
            base_query = base_query.filter(dt_abertura__gte=limite_data)

        total_ordens = base_query.count()
        status_counts = base_query.values('status_ordem_servico').annotate(total=Count('id_ordem_servico'))

        contagens = {
            'ABERTA': 0, 'APROVADA': 0, 'EM_EXECUCAO': 0,
            'AGUARDANDO_MATERIAL': 0, 'AGUARDANDO_TERCEIRO': 0,
            'CONCLUIDA': 0, 'CANCELADA': 0, 'REPROVADA': 0, 'ENCERRADA': 0,
        }
        for item in status_counts:
            if item['status_ordem_servico'] in contagens:
                contagens[item['status_ordem_servico']] = item['total']

        tipo_counts = base_query.values('tipo_manutencao').annotate(total=Count('id_ordem_servico'))
        tipos_dict = {'preventiva': 0, 'corretiva': 0}
        for t in tipo_counts:
            if t['tipo_manutencao'] == 'PREVENTIVA':
                tipos_dict['preventiva'] += t['total']
            else:
                tipos_dict['corretiva'] += t['total']

        ordens_finalizadas = base_query.filter(dt_conclusao__isnull=False, status_ordem_servico__in=['CONCLUIDA', 'ENCERRADA'])
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

        tecnicos_data = []
        try:
            ranking_tecnicos = Usuario.objects.annotate(
                total_os=Count('ordens_atribuidas', filter=Q(ordens_atribuidas__in=base_query)),
                concluidas_os=Count('ordens_atribuidas', filter=Q(ordens_atribuidas__status_ordem_servico__in=['CONCLUIDA', 'ENCERRADA'], ordens_atribuidas__in=base_query))
            ).filter(total_os__gt=0).order_by('-concluidas_os', '-total_os')[:4]
            tecnicos_data = [{'nome': t.nome, 'concluidas': t.concluidas_os, 'total': t.total_os} for t in ranking_tecnicos]
        except Exception:
            pass

        semanas_data = []
        for i in range(5, -1, -1):
            fim_semana = agora - timedelta(weeks=i)
            inicio_semana = fim_semana - timedelta(days=7)
            qtd_semana = base_query.filter(status_ordem_servico__in=['CONCLUIDA', 'ENCERRADA'], dt_conclusao__range=(inicio_semana, fim_semana)).count()
            semanas_data.append({'label': f'Sem {6 - i}', 'valor': qtd_semana})

        return {
            'totalOrdens': total_ordens,
            'abertas': contagens['ABERTA'],
            'emExecucao': contagens['EM_EXECUCAO'],
            'concluidas': contagens['CONCLUIDA'] + contagens['ENCERRADA'],
            'tempo_medio': tempo_medio,
            'statusDetalhados': contagens,
            'tipo_manutencao': tipos_dict,
            'rankingTecnicos': tecnicos_data,
            'pendencias': {
                'aguardando_aprovacao': contagens['ABERTA'],
                'aguardando_material': contagens['AGUARDANDO_MATERIAL'],
                'aguardando_terceiro': contagens['AGUARDANDO_TERCEIRO'],
                'sem_tecnico': base_query.filter(tecnico__isnull=True, status_ordem_servico='APROVADA').count()
            },
            'semanas': semanas_data,
        }


class RegraDashboardGerente(_RegraDashboardBase):
    def _query_base(self, usuario) -> QuerySet:
        return OrdemServico.objects.all()


class RegraDashboardGestor(_RegraDashboardBase):
    def _query_base(self, usuario) -> QuerySet:
        # Regra intencionalmente diferente da listagem: o Gestor também acompanha REPROVADA no dashboard.
        return OrdemServico.objects.filter(
            Q(gestor=usuario) | Q(status_ordem_servico='ABERTA') | Q(status_ordem_servico='REPROVADA')
        )


class RegraDashboardTecnico(_RegraDashboardBase):
    def _query_base(self, usuario) -> QuerySet:
        return OrdemServico.objects.filter(tecnico=usuario)


class RegraDashboardSolicitante(_RegraDashboardBase):
    def _query_base(self, usuario) -> QuerySet:
        return OrdemServico.objects.filter(solicitante=usuario)


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
