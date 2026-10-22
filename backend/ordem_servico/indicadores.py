from collections import Counter
from datetime import datetime, time, timedelta

from django.db.models import Avg, Count, F, Sum
from django.utils import timezone

from ativo.models import Ativo
from ativo.saude import JANELA_REINCIDENCIA_DIAS, saude_dos_ativos
from historico.models import Historico
from ordem_servico.constantes import (
    AGUARDANDO_VALIDACAO,
    CANCELADA,
    EM_EXECUCAO,
    EM_TRIAGEM,
    REABERTA,
    STATUS_ATIVOS,
    STATUS_FINALIZADOS,
    TIPO_CORRETIVA,
    TIPO_PREVENTIVA,
)
from ordem_servico.models import OrdemServico
from validacao.models import ValidacaoAtendimento

PERIODOS = {'30d': 'Últimos 30 dias', 'mes_atual': 'Mês atual', 'mes_passado': 'Mês passado', 'ano': 'Ano atual'}


class PeriodoInvalidoError(Exception):
    pass


def _inicio_do_dia(data):
    return timezone.make_aware(datetime.combine(data, time.min))


def resolver_periodo(periodo=None, inicio=None, fim=None):
    agora = timezone.now()
    hoje = timezone.localdate()
    if inicio or fim:
        try:
            data_inicio = datetime.strptime(inicio, '%Y-%m-%d').date() if inicio else hoje - timedelta(days=30)
            data_fim = datetime.strptime(fim, '%Y-%m-%d').date() if fim else hoje
        except ValueError as erro:
            raise PeriodoInvalidoError("Use datas no formato AAAA-MM-DD.") from erro
        if data_inicio > data_fim:
            raise PeriodoInvalidoError("A data inicial não pode ser posterior à final.")
        return {
            'codigo': 'personalizado',
            'rotulo': f"{data_inicio.strftime('%d/%m/%Y')} a {data_fim.strftime('%d/%m/%Y')}",
            'inicio': _inicio_do_dia(data_inicio),
            'fim': _inicio_do_dia(data_fim + timedelta(days=1)),
        }

    periodo = periodo or '30d'
    if periodo not in PERIODOS:
        raise PeriodoInvalidoError(f"Período inválido. Use: {', '.join(PERIODOS)}.")
    if periodo == 'mes_atual':
        inicio_periodo = _inicio_do_dia(hoje.replace(day=1))
        fim_periodo = agora
    elif periodo == 'mes_passado':
        primeiro_deste_mes = hoje.replace(day=1)
        ultimo_mes_passado = primeiro_deste_mes - timedelta(days=1)
        inicio_periodo = _inicio_do_dia(ultimo_mes_passado.replace(day=1))
        fim_periodo = _inicio_do_dia(primeiro_deste_mes)
    elif periodo == 'ano':
        inicio_periodo = _inicio_do_dia(hoje.replace(month=1, day=1))
        fim_periodo = agora
    else:
        inicio_periodo = agora - timedelta(days=30)
        fim_periodo = agora
    return {'codigo': periodo, 'rotulo': PERIODOS[periodo], 'inicio': inicio_periodo, 'fim': fim_periodo}


def _percentual(parte, total):
    return round(100 * parte / total, 1) if total else None


def _ids_com_reprovacao_ou_reabertura(ids_ordens):
    reprovadas = Historico.objects.filter(
        ordem_servico_id__in=ids_ordens, status_anterior=AGUARDANDO_VALIDACAO, status_novo=EM_EXECUCAO,
    ).values_list('ordem_servico_id', flat=True)
    reabertas = Historico.objects.filter(ordem_servico_id__in=ids_ordens, status_novo=REABERTA).values_list('ordem_servico_id', flat=True)
    return set(reprovadas) | set(reabertas)


def _reincidencias(corretivas_periodo):
    ids_ativos = {os['ativo_id'] for os in corretivas_periodo if os['ativo_id']}
    if not ids_ativos:
        return 0
    anteriores = list(
        OrdemServico.objects.filter(ativo_id__in=ids_ativos, tipo_manutencao=TIPO_CORRETIVA)
        .exclude(status_ordem_servico=CANCELADA)
        .values('id_ordem_servico', 'ativo_id', 'dt_abertura', 'dt_conclusao')
    )
    total = 0
    for atual in corretivas_periodo:
        if not atual['ativo_id']:
            continue
        for outra in anteriores:
            if outra['ativo_id'] != atual['ativo_id'] or outra['id_ordem_servico'] == atual['id_ordem_servico']:
                continue
            referencia = outra['dt_conclusao'] or outra['dt_abertura']
            if referencia <= atual['dt_abertura'] and atual['dt_abertura'] - referencia < timedelta(days=JANELA_REINCIDENCIA_DIAS):
                total += 1
                break
    return total


def calcular_indicadores_gerenciais(periodo):
    inicio, fim = periodo['inicio'], periodo['fim']
    abertas = OrdemServico.objects.com_total_afetados().filter(dt_abertura__gte=inicio, dt_abertura__lt=fim)
    concluidas = OrdemServico.objects.filter(
        status_ordem_servico__in=STATUS_FINALIZADOS, dt_conclusao__gte=inicio, dt_conclusao__lt=fim,
    )
    corretivas_concluidas = concluidas.filter(tipo_manutencao=TIPO_CORRETIVA)

    tempo_medio = concluidas.annotate(duracao=F('dt_conclusao') - F('dt_abertura')).aggregate(media=Avg('duracao'))['media']
    tempo_medio_horas = round(tempo_medio.total_seconds() / 3600, 1) if tempo_medio else None

    mttr = corretivas_concluidas.annotate(duracao=F('dt_conclusao') - F('dt_abertura')).aggregate(media=Avg('duracao'))['media']
    mttr_horas = round(mttr.total_seconds() / 3600, 1) if mttr else None

    ids_corretivas_concluidas = list(corretivas_concluidas.values_list('id_ordem_servico', flat=True))
    com_retrabalho = _ids_com_reprovacao_ou_reabertura(ids_corretivas_concluidas)
    resolvidas_de_primeira = len(ids_corretivas_concluidas) - len(com_retrabalho)

    avaliacoes = ValidacaoAtendimento.objects.filter(nota__isnull=False, dt_validacao__gte=inicio, dt_validacao__lt=fim)
    satisfacao = avaliacoes.aggregate(media=Avg('nota'), total=Count('id_validacao'))

    corretivas_abertas = list(
        abertas.filter(tipo_manutencao=TIPO_CORRETIVA).values('id_ordem_servico', 'ativo_id', 'dt_abertura')
    )
    reincidencias = _reincidencias(corretivas_abertas)

    por_ativo = (
        abertas.filter(ativo__isnull=False)
        .values('ativo_id', 'ativo__codigo_patrimonial', 'ativo__tipo_ativo')
        .annotate(total=Count('id_ordem_servico'))
        .order_by('-total', 'ativo__codigo_patrimonial')[:10]
    )
    por_localizacao = (
        abertas.values('localizacao_id', 'localizacao__desc_localizacao', 'localizacao__predio__nome_predio')
        .annotate(total=Count('id_ordem_servico'))
        .order_by('-total', 'localizacao__desc_localizacao')[:10]
    )
    por_predio = (
        abertas.values('localizacao__predio_id', 'localizacao__predio__nome_predio')
        .annotate(total=Count('id_ordem_servico'))
        .order_by('-total', 'localizacao__predio__nome_predio')[:5]
    )

    saude = saude_dos_ativos(Ativo.objects.all())
    classes_saude = Counter(item['classificacao'] for item in saude)

    return {
        'periodo': {'codigo': periodo['codigo'], 'rotulo': periodo['rotulo'], 'inicio': inicio, 'fim': fim},
        'volume_total': abertas.count(),
        'volume_corretivas': len(corretivas_abertas),
        'volume_preventivas': abertas.filter(tipo_manutencao=TIPO_PREVENTIVA).count(),
        'backlog_ativo': OrdemServico.objects.filter(status_ordem_servico__in=STATUS_ATIVOS, dt_abertura__lt=fim).count(),
        'fila_triagem': OrdemServico.objects.filter(status_ordem_servico__in=(EM_TRIAGEM, REABERTA), dt_abertura__lt=fim).count(),
        'tempo_medio_horas': tempo_medio_horas,
        'total_solucionadas': concluidas.count(),
        'mttr_horas': mttr_horas,
        'taxa_resolucao_primeira_intervencao': _percentual(resolvidas_de_primeira, len(ids_corretivas_concluidas)),
        'satisfacao_media': round(float(satisfacao['media']), 2) if satisfacao['media'] is not None else None,
        'total_avaliacoes': satisfacao['total'],
        'reincidencias': reincidencias,
        'taxa_reincidencia': _percentual(reincidencias, len(corretivas_abertas)),
        'usuarios_afetados': abertas.aggregate(total=Sum('total_afetados_anotado'))['total'] or 0,
        'distribuicao_por_tipo_ativo': [
            {'tipo_ativo': item['ativo__tipo_ativo'], 'total': item['total']}
            for item in abertas.filter(ativo__isnull=False).values('ativo__tipo_ativo').annotate(total=Count('id_ordem_servico')).order_by('ativo__tipo_ativo')
        ],
        'distribuicao_por_ativo': [
            {'id_ativo': item['ativo_id'], 'codigo_patrimonial': item['ativo__codigo_patrimonial'], 'tipo_ativo': item['ativo__tipo_ativo'], 'total': item['total']}
            for item in por_ativo
        ],
        'distribuicao_por_localizacao': [
            {'id_localizacao': item['localizacao_id'], 'localizacao_nome': item['localizacao__desc_localizacao'], 'predio_nome': item['localizacao__predio__nome_predio'], 'total': item['total']}
            for item in por_localizacao
        ],
        'predios_mais_ocorrencias': [
            {'id_predio': item['localizacao__predio_id'], 'predio_nome': item['localizacao__predio__nome_predio'], 'total': item['total']}
            for item in por_predio
        ],
        'saude_ativos': {
            'total_ativos': len(saude),
            'por_classificacao': {codigo: classes_saude.get(codigo, 0) for codigo in ('SAUDAVEL', 'ATENCAO', 'CRITICO', 'MUITO_CRITICO')},
            'nota_media': round(sum(item['nota'] for item in saude) / len(saude), 1) if saude else None,
        },
    }
