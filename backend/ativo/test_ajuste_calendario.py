from datetime import date

import pytest

from ativo.ajuste_calendario import (
    AdiarParaProximoDiaUtil,
    AnteciparParaDiaUtilAnterior,
    ManterDataCalculada,
    resolver_estrategia_ajuste,
)
from ativo.services import calcular_proxima_preventiva

SABADO = date(2026, 9, 5)
SEXTA_ANTERIOR = date(2026, 9, 4)
PROXIMO_DIA_UTIL_APOS_FERIADO = date(2026, 9, 8)


@pytest.mark.parametrize("estrategia, esperado", [
    (AdiarParaProximoDiaUtil(), PROXIMO_DIA_UTIL_APOS_FERIADO),
    (AnteciparParaDiaUtilAnterior(), SEXTA_ANTERIOR),
    (ManterDataCalculada(), SABADO),
])
def test_cada_estrategia_ajusta_o_dia_nao_util_a_sua_maneira(estrategia, esperado):
    assert estrategia.ajustar(SABADO) == esperado


def test_dia_util_nao_e_alterado_por_nenhuma_estrategia():
    for estrategia in (AdiarParaProximoDiaUtil(), AnteciparParaDiaUtilAnterior(), ManterDataCalculada()):
        assert estrategia.ajustar(SEXTA_ANTERIOR) == SEXTA_ANTERIOR


@pytest.mark.parametrize("codigo, classe", [
    ("proximo", AdiarParaProximoDiaUtil),
    ("ANTERIOR", AnteciparParaDiaUtilAnterior),
    ("nenhum", ManterDataCalculada),
    ("desconhecido", AdiarParaProximoDiaUtil),
])
def test_estrategia_e_escolhida_pela_configuracao(settings, codigo, classe):
    settings.PREVENTIVA_AJUSTE_DIA_NAO_UTIL = codigo

    assert isinstance(resolver_estrategia_ajuste(), classe)


def test_calculo_da_preventiva_respeita_a_regra_configurada(settings):
    settings.PREVENTIVA_AJUSTE_DIA_NAO_UTIL = "anterior"
    assert calcular_proxima_preventiva(date(2026, 8, 6), 30) == SEXTA_ANTERIOR

    settings.PREVENTIVA_AJUSTE_DIA_NAO_UTIL = "proximo"
    assert calcular_proxima_preventiva(date(2026, 8, 6), 30) == PROXIMO_DIA_UTIL_APOS_FERIADO

    assert calcular_proxima_preventiva(date(2026, 8, 6), 30, ManterDataCalculada()) == SABADO
