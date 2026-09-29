"""
Processadores de finalização de OrdemServico.

Factory Method: CorretivaFactory/PreventivaFactory decidem qual
ProcessadorOrdemServico finaliza cada tipo de manutenção.

Decorator (padrão estrutural GoF), no final deste módulo:
Antes: a view chamava processador.finalizar() e, logo em seguida, montava o
texto e gravava o histórico da mudança de status por conta própria; log da
operação não existia. Acrescentar qualquer comportamento "em volta" da
finalização exigia mexer na view ou em cada processador concreto.
Depois: ProcessadorDecorator envolve um ProcessadorOrdemServico e expõe a
mesma interface (finalizar), então responsabilidades transversais viram
camadas empilháveis: ComHistoricoDecorator grava o histórico e ComLogDecorator
registra a operação no logging. Os processadores concretos continuam só com a
regra de negócio, e quem monta a pilha é a OrdemServicoFacade.
"""
import logging
import re
from abc import ABC, abstractmethod

from django.utils import timezone

from ativo.models import Ativo
from ativo.services import calcular_proxima_preventiva, criar_ou_atualizar_os_preventiva_para_ativo
from ordem_servico.models import OrdemServico
from utils.historico import registrar_historico

_PADRAO_PATRIMONIO = re.compile(r'\[PAT:\s*([^\]]+)\]')

logger = logging.getLogger(__name__)


class ProcessadorOrdemServico(ABC):
    """Produto do Factory Method: cada tipo de manutenção sabe finalizar sua própria OS."""

    @abstractmethod
    def finalizar(self, ordem_servico: OrdemServico, motivo_tecnico: str) -> None:
        """Aplica, em memória, as regras de finalização; quem chama decide quando salvar."""
        ...


class _ProcessadorOrdemServicoBase(ProcessadorOrdemServico):
    """Comportamento comum aos dois tipos: vincular o ativo pela tag [PAT: ...] e recalcular a preventiva dele."""

    def _concluir(self, ordem_servico: OrdemServico, motivo_tecnico: str) -> None:
        ordem_servico.dt_conclusao = timezone.now()
        self._vincular_ativo_pela_observacao(ordem_servico, motivo_tecnico)
        self._atualizar_manutencao_do_ativo(ordem_servico)

    @staticmethod
    def _vincular_ativo_pela_observacao(ordem_servico: OrdemServico, motivo_tecnico: str) -> None:
        match = _PADRAO_PATRIMONIO.search(motivo_tecnico or "")
        if not match:
            return

        patrimonio_informado = match.group(1).strip()
        ativo_vinculado = Ativo.objects.filter(codigo_patrimonial=patrimonio_informado).first()
        if ativo_vinculado:
            ordem_servico.ativo = ativo_vinculado

    @staticmethod
    def _atualizar_manutencao_do_ativo(ordem_servico: OrdemServico) -> None:
        if not ordem_servico.ativo:
            return

        ativo = ordem_servico.ativo
        ativo.dt_ultima_preventiva = timezone.now().date()

        if ativo.periodicidade_preventiva_dias:
            ativo.dt_proxima_preventiva = calcular_proxima_preventiva(
                ativo.dt_ultima_preventiva,
                ativo.periodicidade_preventiva_dias,
                ativo.localizacao,
                ativo,
            )

        ativo.save()
        criar_ou_atualizar_os_preventiva_para_ativo(ativo)


class ProcessadorCorretiva(_ProcessadorOrdemServicoBase):
    def finalizar(self, ordem_servico: OrdemServico, motivo_tecnico: str) -> None:
        if ordem_servico.status_ordem_servico == "CONCLUIDA":
            self._concluir(ordem_servico, motivo_tecnico)


class ProcessadorPreventiva(_ProcessadorOrdemServicoBase):
    def finalizar(self, ordem_servico: OrdemServico, motivo_tecnico: str) -> None:
        if ordem_servico.status_ordem_servico == "CONCLUIDA":
            self._concluir(ordem_servico, motivo_tecnico)
            ordem_servico.status_ordem_servico = "ENCERRADA"


class ProcessadorOrdemServicoFactory(ABC):
    """Fábrica abstrata: o factory method decide qual Processador usar para o tipo de manutenção."""

    @abstractmethod
    def criar_processador(self) -> ProcessadorOrdemServico:
        ...


class CorretivaFactory(ProcessadorOrdemServicoFactory):
    def criar_processador(self) -> ProcessadorOrdemServico:
        return ProcessadorCorretiva()


class PreventivaFactory(ProcessadorOrdemServicoFactory):
    def criar_processador(self) -> ProcessadorOrdemServico:
        return ProcessadorPreventiva()


_FABRICAS_POR_TIPO_MANUTENCAO = {
    "CORRETIVA": CorretivaFactory,
    "PREVENTIVA": PreventivaFactory,
}


def obter_fabrica_processador(tipo_manutencao: str) -> ProcessadorOrdemServicoFactory:
    """Resolve a fábrica pelo tipo de manutenção; CORRETIVA é o default (mesmo comportamento do model)."""
    fabrica_cls = _FABRICAS_POR_TIPO_MANUTENCAO.get(tipo_manutencao, CorretivaFactory)
    return fabrica_cls()


class ProcessadorDecorator(ProcessadorOrdemServico):
    """Decorator abstrato: tem a mesma interface do processador e delega a ele o trabalho real."""

    def __init__(self, processador: ProcessadorOrdemServico) -> None:
        self._processador = processador

    @property
    def processador_envolvido(self) -> ProcessadorOrdemServico:
        return self._processador

    @abstractmethod
    def finalizar(self, ordem_servico: OrdemServico, motivo_tecnico: str) -> None:
        self._processador.finalizar(ordem_servico, motivo_tecnico)


class ComHistoricoDecorator(ProcessadorDecorator):
    """Grava no histórico a mudança de status que está sendo processada."""

    def __init__(self, processador: ProcessadorOrdemServico, usuario, status_anterior: str) -> None:
        super().__init__(processador)
        self._usuario = usuario
        self._status_anterior = status_anterior

    def finalizar(self, ordem_servico: OrdemServico, motivo_tecnico: str) -> None:
        novo_status = ordem_servico.status_ordem_servico

        super().finalizar(ordem_servico, motivo_tecnico)

        registrar_historico(ordem_servico, self._usuario, self._montar_texto(novo_status, motivo_tecnico))

    def _montar_texto(self, novo_status: str, motivo_tecnico: str) -> str:
        texto_historico = f"Status alterado: {self._status_anterior} -> {novo_status}."
        if motivo_tecnico and str(motivo_tecnico).strip():
            texto_historico += f" Detalhes: {str(motivo_tecnico).strip()}"
        return texto_historico


class ComLogDecorator(ProcessadorDecorator):
    """Registra no logging o início, o fim e eventuais falhas da finalização."""

    def __init__(self, processador: ProcessadorOrdemServico, logger_operacao: logging.Logger | None = None) -> None:
        super().__init__(processador)
        self._logger = logger_operacao or logger

    def finalizar(self, ordem_servico: OrdemServico, motivo_tecnico: str) -> None:
        self._logger.info(
            "Finalizando OS #%s (%s) com status %s.",
            ordem_servico.pk, ordem_servico.tipo_manutencao, ordem_servico.status_ordem_servico,
        )
        try:
            super().finalizar(ordem_servico, motivo_tecnico)
        except Exception:
            self._logger.exception("Falha ao finalizar OS #%s.", ordem_servico.pk)
            raise

        self._logger.info(
            "OS #%s processada; status final %s.",
            ordem_servico.pk, ordem_servico.status_ordem_servico,
        )
