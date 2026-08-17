from datetime import timedelta, date
import holidays
from ativo.models import Ativo
from django.utils import timezone

feriados_br = holidays.Brazil()

def ajustar_para_dia_util(data):
    while data.weekday() >= 5 or data in feriados_br:
        data += timedelta(days=1)

    return data


def adicionar_meses(data, meses):
    mes = data.month - 1 + meses
    ano = data.year + mes // 12
    mes = mes % 12 + 1

    return date(ano, mes, 1)


def existe_outro_predio_no_mes(predio_atual, data_referencia):
    ativos_no_mes = Ativo.objects.filter(dt_proxima_preventiva__year=data_referencia.year, dt_proxima_preventiva__month=data_referencia.month).select_related('localizacao__predio')

    for ativo in ativos_no_mes:
        if ativo.localizacao.predio_id != predio_atual.id_predio:
            return True

    return False


def predio_ja_tem_preventiva_no_mes(predio_atual, data_referencia, ativo_atual=None):
    queryset = Ativo.objects.filter( localizacao__predio=predio_atual, dt_proxima_preventiva__year=data_referencia.year, dt_proxima_preventiva__month=data_referencia.month)

    if ativo_atual:
        queryset = queryset.exclude(id_ativo=ativo_atual.id_ativo)

    return queryset.exists()


def calcular_proxima_preventiva(dt_ultima_preventiva,periodicidade_dias,localizacao=None,ativo_atual=None):
    data_calculada = dt_ultima_preventiva + timedelta(days=periodicidade_dias)
    data_calculada = date(data_calculada.year, data_calculada.month, 1)

    if not localizacao:
        return ajustar_para_dia_util(data_calculada)

    predio_atual = localizacao.predio

    for i in range(12):
        data_tentativa = adicionar_meses(data_calculada, i)

        if predio_ja_tem_preventiva_no_mes(predio_atual,data_tentativa,ativo_atual):
            return ajustar_para_dia_util(data_tentativa)

        if not existe_outro_predio_no_mes(predio_atual,data_tentativa):
            return ajustar_para_dia_util(data_tentativa)

    return ajustar_para_dia_util(data_calculada)

def criar_ou_atualizar_os_preventiva_para_ativo(ativo):
    from ordem_servico.models import OrdemServico

    if not ativo.dt_proxima_preventiva:
        return None

    descricao = (
        f"Manutenção preventiva programada automaticamente para o ativo "
        f"{ativo.codigo_patrimonial or ativo.id_ativo}, prevista para "
        f"{ativo.dt_proxima_preventiva.strftime('%d/%m/%Y')}."
    )

    os_existente = OrdemServico.objects.filter(
        ativo=ativo,
        tipo_manutencao='PREVENTIVA',
        status_ordem_servico__in=['ABERTA', 'APROVADA']
    ).first()

    if os_existente:
        os_existente.localizacao = ativo.localizacao
        os_existente.categoria_manutencao = 'GERAIS'
        os_existente.prioridade_urgencia = 'NAO'
        os_existente.descricao_servico = descricao
        os_existente.save()
        return os_existente

    return OrdemServico.objects.create(
        localizacao=ativo.localizacao,
        ativo=ativo,
        solicitante=None,
        tipo_manutencao='PREVENTIVA',
        categoria_manutencao='GERAIS',
        prioridade_urgencia='NAO',
        status_ordem_servico='ABERTA',
        dt_abertura=timezone.now(),
        descricao_servico=descricao
    )