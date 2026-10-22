from abc import ABC, abstractmethod

from django.utils import timezone

from ordem_servico.constantes import EM_TRIAGEM, PRIORIDADE_NORMAL, TIPO_CORRETIVA, TIPO_PREVENTIVA
from ordem_servico.models import OrdemServico


class IOrdemServicoBuilder(ABC):
    @abstractmethod
    def com_localizacao(self, localizacao) -> "IOrdemServicoBuilder": ...

    @abstractmethod
    def com_solicitante(self, usuario) -> "IOrdemServicoBuilder": ...

    @abstractmethod
    def com_ativo(self, ativo) -> "IOrdemServicoBuilder": ...

    @abstractmethod
    def como_corretiva(self, categoria_manutencao, prioridade_urgencia) -> "IOrdemServicoBuilder": ...

    @abstractmethod
    def como_preventiva(self) -> "IOrdemServicoBuilder": ...

    @abstractmethod
    def com_descricao(self, texto) -> "IOrdemServicoBuilder": ...

    @abstractmethod
    def construir(self) -> OrdemServico: ...


class OrdemServicoBuilder(IOrdemServicoBuilder):
    def __init__(self) -> None:
        self._dados = {
            "status_ordem_servico": EM_TRIAGEM,
            "dt_abertura": timezone.now(),
        }

    def com_localizacao(self, localizacao) -> "OrdemServicoBuilder":
        self._dados["localizacao"] = localizacao
        return self

    def com_solicitante(self, usuario) -> "OrdemServicoBuilder":
        self._dados["solicitante"] = usuario
        return self

    def com_ativo(self, ativo) -> "OrdemServicoBuilder":
        self._dados["ativo"] = ativo
        return self

    def como_corretiva(self, categoria_manutencao=None, prioridade_urgencia=None) -> "OrdemServicoBuilder":
        self._dados["tipo_manutencao"] = TIPO_CORRETIVA
        self._dados["categoria_manutencao"] = categoria_manutencao
        self._dados["prioridade_urgencia"] = prioridade_urgencia or PRIORIDADE_NORMAL
        return self

    def como_preventiva(self) -> "OrdemServicoBuilder":
        self._dados["tipo_manutencao"] = TIPO_PREVENTIVA
        self._dados["categoria_manutencao"] = "GERAIS"
        self._dados["prioridade_urgencia"] = PRIORIDADE_NORMAL
        return self

    def com_descricao(self, texto) -> "OrdemServicoBuilder":
        self._dados["descricao_servico"] = texto
        return self

    def construir(self) -> OrdemServico:
        return OrdemServico(**self._dados)


class OrdemServicoDiretor:
    """Conhece os dois fluxos reais de criação de OrdemServico e monta cada um com o Builder correto."""

    def __init__(self, builder_factory=OrdemServicoBuilder) -> None:
        self._builder_factory = builder_factory

    def construir_corretiva_do_solicitante(
        self,
        usuario,
        localizacao,
        descricao,
        categoria_manutencao=None,
        prioridade_urgencia=None,
        **campos_extra,
    ) -> OrdemServico:
        ordem_servico = (
            self._builder_factory()
            .com_localizacao(localizacao)
            .com_solicitante(usuario)
            .como_corretiva(categoria_manutencao, prioridade_urgencia)
            .com_descricao(descricao)
            .construir()
        )

        for campo, valor in campos_extra.items():
            setattr(ordem_servico, campo, valor)

        ordem_servico.save()
        return ordem_servico

    def construir_preventiva_agrupada(self, localizacao, descricao) -> OrdemServico:
        ordem_servico = (
            self._builder_factory()
            .com_localizacao(localizacao)
            .como_preventiva()
            .com_descricao(descricao)
            .construir()
        )
        ordem_servico.save()
        return ordem_servico
