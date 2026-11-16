from abc import ABC, abstractmethod
from datetime import date

from django.conf import settings

from ativo.calendario_feriados import GerenciadorCalendarioFeriados


class EstrategiaAjusteDiaNaoUtil(ABC):
    codigo = ''

    def __init__(self, calendario=None):
        self._calendario = calendario or GerenciadorCalendarioFeriados.instancia()

    @abstractmethod
    def ajustar(self, data: date) -> date:
        ...


class AdiarParaProximoDiaUtil(EstrategiaAjusteDiaNaoUtil):
    codigo = 'proximo'

    def ajustar(self, data):
        return self._calendario.proximo_dia_util(data)


class AnteciparParaDiaUtilAnterior(EstrategiaAjusteDiaNaoUtil):
    codigo = 'anterior'

    def ajustar(self, data):
        return self._calendario.dia_util_anterior(data)


class ManterDataCalculada(EstrategiaAjusteDiaNaoUtil):
    codigo = 'nenhum'

    def ajustar(self, data):
        return data


ESTRATEGIAS_AJUSTE = {
    estrategia.codigo: estrategia
    for estrategia in (AdiarParaProximoDiaUtil, AnteciparParaDiaUtilAnterior, ManterDataCalculada)
}


def resolver_estrategia_ajuste(codigo=None) -> EstrategiaAjusteDiaNaoUtil:
    codigo = (codigo or settings.PREVENTIVA_AJUSTE_DIA_NAO_UTIL or AdiarParaProximoDiaUtil.codigo).strip().lower()
    return ESTRATEGIAS_AJUSTE.get(codigo, AdiarParaProximoDiaUtil)()
