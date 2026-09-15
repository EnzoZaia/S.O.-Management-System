from datetime import timedelta, date
from ativo.calendario_feriados import GerenciadorCalendarioFeriados
from ativo.models import Ativo
from ordem_servico.builders import OrdemServicoDiretor


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
        return GerenciadorCalendarioFeriados.instancia().proximo_dia_util(data_calculada)

    calendario = GerenciadorCalendarioFeriados.instancia()
    predio_atual = localizacao.predio

    for i in range(12):
        data_tentativa = adicionar_meses(data_calculada, i)

        if predio_ja_tem_preventiva_no_mes(predio_atual,data_tentativa,ativo_atual):
            return calendario.proximo_dia_util(data_tentativa)

        if not existe_outro_predio_no_mes(predio_atual,data_tentativa):
            return calendario.proximo_dia_util(data_tentativa)

    return calendario.proximo_dia_util(data_calculada)

def criar_ou_atualizar_os_preventiva_para_ativo(ativo):
    return OrdemServicoDiretor().construir_preventiva_automatica(ativo)