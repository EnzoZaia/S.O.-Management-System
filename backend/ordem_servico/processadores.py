import re
from abc import ABC, abstractmethod

from django.utils import timezone

from ativo.models import Ativo
from ativo.services import calcular_proxima_preventiva, criar_ou_atualizar_os_preventiva_para_ativo
from ordem_servico.models import OrdemServico

_PADRAO_PATRIMONIO = re.compile(r'\[PAT:\s*([^\]]+)\]')


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
