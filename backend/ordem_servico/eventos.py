import logging
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass

from django.db import transaction

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class EventoOrdemServico:
    ordem_servico: object
    responsavel: object


@dataclass(frozen=True)
class TecnicoAtribuido(EventoOrdemServico):
    tecnico: object


@dataclass(frozen=True)
class TecnicoReatribuido(EventoOrdemServico):
    tecnico: object
    tecnico_anterior: object
    justificativa: str


@dataclass(frozen=True)
class ServicoReprovado(EventoOrdemServico):
    justificativa: str | None


class Observador(ABC):
    @abstractmethod
    def atualizar(self, evento: EventoOrdemServico) -> None:
        ...


class PublicadorEventos:
    def __init__(self):
        self._observadores = defaultdict(list)

    def inscrever(self, tipo_evento, observador: Observador) -> "PublicadorEventos":
        if observador not in self._observadores[tipo_evento]:
            self._observadores[tipo_evento].append(observador)
        return self

    def cancelar_inscricao(self, tipo_evento, observador: Observador) -> None:
        if observador in self._observadores[tipo_evento]:
            self._observadores[tipo_evento].remove(observador)

    def observadores_de(self, tipo_evento):
        return tuple(self._observadores[tipo_evento])

    def publicar(self, evento: EventoOrdemServico) -> None:
        for observador in self.observadores_de(type(evento)):
            try:
                with transaction.atomic():
                    observador.atualizar(evento)
            except Exception:
                logger.exception(
                    "Observador %s falhou ao tratar %s da OS #%s.",
                    type(observador).__name__, type(evento).__name__, getattr(evento.ordem_servico, 'pk', None),
                )
