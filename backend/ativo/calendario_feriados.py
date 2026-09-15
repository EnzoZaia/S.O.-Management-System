from datetime import date, timedelta

import holidays


class _SingletonMeta(type):
    _instancias: dict = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instancias:
            cls._instancias[cls] = super().__call__(*args, **kwargs)
        return cls._instancias[cls]

    def resetar_instancia(cls) -> None:
        """Uso exclusivo em testes: descarta a instância para evitar vazamento de estado entre casos de teste."""
        cls._instancias.pop(cls, None)


class GerenciadorCalendarioFeriados(metaclass=_SingletonMeta):
    """Ponto único de acesso ao calendário de feriados nacionais."""

    def __init__(self) -> None:
        self._feriados = holidays.Brazil()

    @classmethod
    def instancia(cls) -> "GerenciadorCalendarioFeriados":
        return cls()

    def eh_dia_nao_util(self, data: date) -> bool:
        return data.weekday() >= 5 or data in self._feriados

    def proximo_dia_util(self, data: date) -> date:
        while self.eh_dia_nao_util(data):
            data += timedelta(days=1)
        return data
