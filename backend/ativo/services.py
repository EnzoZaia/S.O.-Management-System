from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from ativo.calendario_feriados import GerenciadorCalendarioFeriados


def intervalo_preventiva_dias(tipo_ativo, id_predio=None):
    if id_predio:
        from preventiva_grupo.models import PlanoManutencaoPreventiva

        ciclo = (
            PlanoManutencaoPreventiva.objects.filter(predio_id=id_predio, tipo_ativo=tipo_ativo, ativo_no_sistema=True)
            .values_list('ciclo_dias', flat=True)
            .first()
        )
        if ciclo:
            return ciclo
    return settings.INTERVALO_PREVENTIVA_DIAS.get(tipo_ativo, settings.INTERVALO_PREVENTIVA_PADRAO_DIAS)


def calcular_proxima_preventiva(dt_ultima_preventiva, periodicidade_dias):
    data_base = dt_ultima_preventiva + timedelta(days=periodicidade_dias)
    return GerenciadorCalendarioFeriados.instancia().proximo_dia_util(data_base)


def recalcular_programacao(ativo, data_base=None):
    referencia = ativo.dt_ultima_preventiva or data_base or timezone.localdate()
    ativo.dt_proxima_preventiva = calcular_proxima_preventiva(referencia, ativo.periodicidade_preventiva_dias)
    return ativo.dt_proxima_preventiva


def registrar_preventiva_concluida(ativo, data_conclusao=None):
    ativo.dt_ultima_preventiva = data_conclusao or timezone.localdate()
    recalcular_programacao(ativo)
    ativo.save(update_fields=['dt_ultima_preventiva', 'dt_proxima_preventiva'])
    return ativo


def alerta_preventiva_proxima(ativo, data_referencia=None):
    if ativo is None or ativo.dt_proxima_preventiva is None:
        return None
    referencia = data_referencia or timezone.localdate()
    dias = (ativo.dt_proxima_preventiva - referencia).days
    if 0 <= dias <= settings.DIAS_ALERTA_PREVENTIVA_PROXIMA:
        return {
            'dt_proxima_preventiva': ativo.dt_proxima_preventiva,
            'dias_para_preventiva': dias,
            'mensagem': (
                f"A preventiva deste ativo está prevista para {ativo.dt_proxima_preventiva.strftime('%d/%m/%Y')} "
                f"(em {dias} dia(s)). Avalie executar a corretiva junto com a preventiva."
            ),
        }
    return None
