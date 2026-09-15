from datetime import date

from ativo.calendario_feriados import GerenciadorCalendarioFeriados


def teardown_function(_função):
    GerenciadorCalendarioFeriados.resetar_instancia()


def test_instancia_e_singleton():
    primeira = GerenciadorCalendarioFeriados.instancia()
    segunda = GerenciadorCalendarioFeriados.instancia()

    assert primeira is segunda


def test_resetar_instancia_cria_nova_instancia():
    primeira = GerenciadorCalendarioFeriados.instancia()

    GerenciadorCalendarioFeriados.resetar_instancia()

    segunda = GerenciadorCalendarioFeriados.instancia()

    assert primeira is not segunda


def test_sabado_e_domingo_sao_dias_nao_uteis():
    calendario = GerenciadorCalendarioFeriados.instancia()

    sabado = date(2026, 9, 5)
    domingo = date(2026, 9, 6)

    assert calendario.eh_dia_nao_util(sabado) is True
    assert calendario.eh_dia_nao_util(domingo) is True


def test_feriado_nacional_conhecido_e_dia_nao_util():
    calendario = GerenciadorCalendarioFeriados.instancia()

    natal = date(2026, 12, 25)

    assert calendario.eh_dia_nao_util(natal) is True


def test_dia_util_comum_nao_e_marcado_como_nao_util():
    calendario = GerenciadorCalendarioFeriados.instancia()

    terca_comum = date(2026, 9, 8)

    assert calendario.eh_dia_nao_util(terca_comum) is False


def test_proximo_dia_util_avanca_cruzando_fim_de_semana_e_feriado():
    calendario = GerenciadorCalendarioFeriados.instancia()

    # Sábado 05/09/2026 -> domingo 06 -> segunda 07 é feriado (Independência) -> terça 08
    sabado = date(2026, 9, 5)
    proximo_util_esperado = date(2026, 9, 8)

    assert calendario.proximo_dia_util(sabado) == proximo_util_esperado


def test_proximo_dia_util_mantem_dia_ja_util():
    calendario = GerenciadorCalendarioFeriados.instancia()

    terca_comum = date(2026, 9, 8)

    assert calendario.proximo_dia_util(terca_comum) == terca_comum
