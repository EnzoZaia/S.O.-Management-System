from abc import ABC, abstractmethod

from django.utils import timezone

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
            "status_ordem_servico": "ABERTA",
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
        self._dados["tipo_manutencao"] = "CORRETIVA"
        self._dados["categoria_manutencao"] = categoria_manutencao
        self._dados["prioridade_urgencia"] = prioridade_urgencia
        return self

    def como_preventiva(self) -> "OrdemServicoBuilder":
        self._dados["tipo_manutencao"] = "PREVENTIVA"
        self._dados["categoria_manutencao"] = "GERAIS"
        self._dados["prioridade_urgencia"] = "NAO"
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

    def construir_preventiva_automatica(self, ativo) -> OrdemServico | None:
        if not ativo.dt_proxima_preventiva:
            return None

        descricao = (
            f"Manutenção preventiva programada automaticamente para o ativo "
            f"{ativo.codigo_patrimonial or ativo.id_ativo}, prevista para "
            f"{ativo.dt_proxima_preventiva.strftime('%d/%m/%Y')}."
        )

        os_montada = (
            self._builder_factory()
            .com_localizacao(ativo.localizacao)
            .com_ativo(ativo)
            .como_preventiva()
            .com_descricao(descricao)
            .construir()
        )

        os_existente = OrdemServico.objects.filter(
            ativo=ativo,
            tipo_manutencao="PREVENTIVA",
            status_ordem_servico__in=["ABERTA", "APROVADA"],
        ).first()

        if os_existente:
            os_existente.localizacao = os_montada.localizacao
            os_existente.categoria_manutencao = os_montada.categoria_manutencao
            os_existente.prioridade_urgencia = os_montada.prioridade_urgencia
            os_existente.descricao_servico = os_montada.descricao_servico
            os_existente.save()
            return os_existente

        os_montada.save()
        return os_montada
