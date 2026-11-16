from notificacao.services import TIPO_OS_ATRIBUIDA, TIPO_OS_REATRIBUIDA, TIPO_OS_REPROVADA, notificar
from ordem_servico.eventos import (
    Observador,
    PublicadorEventos,
    ServicoReprovado,
    TecnicoAtribuido,
    TecnicoReatribuido,
)
from utils.historico import registrar_historico

TAMANHO_RESUMO_PROBLEMA = 120


class NotificarNovoTecnicoObserver(Observador):
    def __init__(self, notificador=notificar):
        self._notificar = notificador

    def atualizar(self, evento):
        ordem_servico = evento.ordem_servico
        resumo = (ordem_servico.descricao_servico or "")[:TAMANHO_RESUMO_PROBLEMA]
        self._notificar(
            evento.tecnico, TIPO_OS_ATRIBUIDA, f"OS #{ordem_servico.pk} atribuída a você",
            f"A ordem de serviço #{ordem_servico.pk} foi atribuída a você. Problema: {resumo}",
            ordem_servico,
        )


class NotificarTecnicoAnteriorObserver(Observador):
    def __init__(self, notificador=notificar):
        self._notificar = notificador

    def atualizar(self, evento):
        if evento.tecnico_anterior is None:
            return
        ordem_servico = evento.ordem_servico
        self._notificar(
            evento.tecnico_anterior, TIPO_OS_REATRIBUIDA, f"OS #{ordem_servico.pk} reatribuída",
            f"A ordem de serviço #{ordem_servico.pk} foi reatribuída para {evento.tecnico.nome}. Justificativa: {evento.justificativa}",
            ordem_servico,
        )


class AlertarGestorReprovacaoObserver(Observador):
    def __init__(self, notificador=notificar, historico=registrar_historico):
        self._notificar = notificador
        self._registrar_historico = historico

    def atualizar(self, evento):
        ordem_servico = evento.ordem_servico
        gestor = ordem_servico.gestor
        if gestor is None:
            self._registrar_historico(ordem_servico, evento.responsavel, "Alerta de reprovação: OS sem gestor definido; nenhum e-mail enviado.")
            return

        self._registrar_historico(ordem_servico, evento.responsavel, f"Alerta de reprovação enviado ao gestor {gestor.nome}.")
        self._notificar(
            gestor, TIPO_OS_REPROVADA, f"OS #{ordem_servico.pk} reprovada pelo solicitante",
            f"Olá, {gestor.nome}.\n\n"
            f"A ordem de serviço #{ordem_servico.pk} foi reprovada por {evento.responsavel.nome} e voltou para execução.\n\n"
            f"Justificativa: {evento.justificativa}",
            ordem_servico,
        )


def criar_publicador_padrao() -> PublicadorEventos:
    novo_tecnico = NotificarNovoTecnicoObserver()
    return (
        PublicadorEventos()
        .inscrever(TecnicoAtribuido, novo_tecnico)
        .inscrever(TecnicoReatribuido, novo_tecnico)
        .inscrever(TecnicoReatribuido, NotificarTecnicoAnteriorObserver())
        .inscrever(ServicoReprovado, AlertarGestorReprovacaoObserver())
    )
