from collections import defaultdict
from datetime import timedelta

from django.utils import timezone

from ordem_servico.constantes import (
    CANCELADA,
    PRIORIDADE_URGENTE,
    STATUS_FINALIZADOS,
    TIPO_CORRETIVA,
)
from ordem_servico.models import OrdemServico

NOTA_INICIAL = 100
PENALIDADE_PREVENTIVA_ATRASADA = 25
PENALIDADE_CORRETIVA_RECENTE = 10
PENALIDADE_REINCIDENCIA = 15
PENALIDADE_URGENCIA_RECENTE = 20
JANELA_CORRETIVAS_DIAS = 60
JANELA_REINCIDENCIA_DIAS = 15
JANELA_URGENCIA_DIAS = 30

CLASSIFICACOES = (
    (80, 'SAUDAVEL', 'Saudável'),
    (60, 'ATENCAO', 'Atenção'),
    (40, 'CRITICO', 'Crítico'),
    (0, 'MUITO_CRITICO', 'Muito Crítico'),
)


def classificar(nota):
    for minimo, codigo, rotulo in CLASSIFICACOES:
        if nota >= minimo:
            return codigo, rotulo
    return CLASSIFICACOES[-1][1], CLASSIFICACOES[-1][2]


def _corretivas_por_ativo(ids_ativos, desde):
    agrupadas = defaultdict(list)
    consulta = (
        OrdemServico.objects.filter(ativo_id__in=ids_ativos, tipo_manutencao=TIPO_CORRETIVA, dt_abertura__gte=desde)
        .exclude(status_ordem_servico=CANCELADA)
        .values('ativo_id', 'id_ordem_servico', 'dt_abertura', 'dt_conclusao', 'status_ordem_servico', 'prioridade_urgencia')
        .order_by('dt_abertura')
    )
    for linha in consulta:
        agrupadas[linha['ativo_id']].append(linha)
    return agrupadas


def _reincidencias(corretivas):
    total = 0
    anteriores = []
    for atual in corretivas:
        for anterior in anteriores:
            referencia = anterior['dt_conclusao'] or anterior['dt_abertura']
            if referencia <= atual['dt_abertura'] and atual['dt_abertura'] - referencia < timedelta(days=JANELA_REINCIDENCIA_DIAS):
                total += 1
                break
        anteriores.append(atual)
    return total


def calcular_saude(ativo, corretivas, agora=None):
    agora = agora or timezone.now()
    hoje = timezone.localdate()
    fatores = []

    if ativo.dt_proxima_preventiva and ativo.dt_proxima_preventiva < hoje:
        dias = (hoje - ativo.dt_proxima_preventiva).days
        fatores.append({
            'fator': 'PREVENTIVA_ATRASADA', 'quantidade': 1, 'pontos': -PENALIDADE_PREVENTIVA_ATRASADA,
            'descricao': f'Preventiva atrasada há {dias} dia(s).',
        })

    limite_corretivas = agora - timedelta(days=JANELA_CORRETIVAS_DIAS)
    encerradas = [
        os for os in corretivas
        if os['status_ordem_servico'] in STATUS_FINALIZADOS and os['dt_conclusao'] and os['dt_conclusao'] >= limite_corretivas
    ]
    if encerradas:
        fatores.append({
            'fator': 'CORRETIVAS_RECENTES', 'quantidade': len(encerradas),
            'pontos': -PENALIDADE_CORRETIVA_RECENTE * len(encerradas),
            'descricao': f'{len(encerradas)} corretiva(s) encerrada(s) nos últimos {JANELA_CORRETIVAS_DIAS} dias.',
        })

    janela = [os for os in corretivas if os['dt_abertura'] >= limite_corretivas]
    reincidencias = _reincidencias(janela)
    if reincidencias:
        fatores.append({
            'fator': 'REINCIDENCIA', 'quantidade': reincidencias,
            'pontos': -PENALIDADE_REINCIDENCIA * reincidencias,
            'descricao': f'{reincidencias} reincidência(s) em menos de {JANELA_REINCIDENCIA_DIAS} dias.',
        })

    limite_urgencia = agora - timedelta(days=JANELA_URGENCIA_DIAS)
    urgentes = [os for os in corretivas if os['prioridade_urgencia'] == PRIORIDADE_URGENTE and os['dt_abertura'] >= limite_urgencia]
    if urgentes:
        fatores.append({
            'fator': 'OCORRENCIA_URGENTE', 'quantidade': len(urgentes), 'pontos': -PENALIDADE_URGENCIA_RECENTE,
            'descricao': f'{len(urgentes)} ocorrência(s) urgente(s) no último mês.',
        })

    nota = max(0, min(NOTA_INICIAL, NOTA_INICIAL + sum(fator['pontos'] for fator in fatores)))
    codigo, rotulo = classificar(nota)
    return {
        'id_ativo': ativo.id_ativo,
        'codigo_patrimonial': ativo.codigo_patrimonial,
        'tipo_ativo': ativo.tipo_ativo,
        'nota': nota,
        'classificacao': codigo,
        'classificacao_rotulo': rotulo,
        'fatores': fatores,
    }


def saude_dos_ativos(ativos):
    ativos = list(ativos)
    agora = timezone.now()
    desde = agora - timedelta(days=JANELA_CORRETIVAS_DIAS + JANELA_REINCIDENCIA_DIAS)
    corretivas = _corretivas_por_ativo([ativo.id_ativo for ativo in ativos], desde)
    return [calcular_saude(ativo, corretivas.get(ativo.id_ativo, []), agora) for ativo in ativos]
