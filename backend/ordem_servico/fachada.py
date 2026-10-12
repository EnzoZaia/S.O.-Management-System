"""
Façade (padrão estrutural GoF) para as operações de escrita sobre OrdemServico.

Antes: cada view de ordem_servico/views.py conhecia e orquestrava, por conta
própria, o Diretor/Builder (abertura), a fábrica de processadores (mudança de
status), o registrar_historico (em quatro lugares diferentes, cada um com seu
texto) e a regra de status finais (ENCERRADA/CANCELADA), que estava duplicada
em update() e destroy(). Para entender "o que acontece quando uma OS muda de
status" era preciso ler a view inteira.

Depois: OrdemServicoFacade é o ponto único de entrada desses fluxos. As views
só validam entrada/permissões e chamam abrir(), alterar_status(),
atribuir_tecnico() ou cancelar(); a fachada decide quais subsistemas acionar,
em que ordem e dentro de uma transação. Os subsistemas (Builder, Factory
Method, Decorators, histórico) continuam independentes e testáveis sozinhos:
a fachada não os substitui, só os coordena.
"""
import logging

from django.conf import settings
from django.core.mail import send_mail
from django.db import IntegrityError, transaction
from django.utils import timezone

from ativo.models import Ativo
from ordem_servico.builders import OrdemServicoDiretor
from ordem_servico.constantes import (
    ABERTA,
    AGUARDANDO_VALIDACAO,
    APROVADA,
    CANCELADA,
    CONCLUIDA,
    EM_EXECUCAO,
    ENCERRADA,
    STATUS_FINAIS,
    status_para_api,
)
from ordem_servico.models import OrdemServico
from ordem_servico.participacao import corretiva_ativa_do_ativo, os_esta_ativa, usuario_ja_vinculado
from os_participante.models import OsParticipante
from ordem_servico.processadores import (
    ComHistoricoDecorator,
    ComLogDecorator,
    ProcessadorOrdemServico,
    obter_fabrica_processador,
)
from utils.historico import (
    definir_usuario_da_sessao,
    registrar_atribuicao,
    registrar_historico,
    registrar_mudanca_status,
)
from utils.permissions import usuario_tem_grupo
from validacao.models import RESULTADO_APROVADA, RESULTADO_REPROVADA, EvidenciaValidacao, ValidacaoAtendimento

logger = logging.getLogger(__name__)


class OperacaoOrdemServicoError(Exception):
    """Regra de negócio violada numa operação da fachada; a mensagem vai direto para o cliente da API."""

    def __init__(self, mensagem: str) -> None:
        super().__init__(mensagem)
        self.mensagem = mensagem


class OrdemServicoStatusFinalError(OperacaoOrdemServicoError):
    """A OS já está ENCERRADA ou CANCELADA e não aceita mais a operação pedida."""


class TecnicoInvalidoError(OperacaoOrdemServicoError):
    """O usuário indicado para a atribuição não pertence ao grupo TECNICO."""


class OrdemServicoStatusInvalidoError(OperacaoOrdemServicoError):
    pass


class CorretivaDuplicadaError(OperacaoOrdemServicoError):
    def __init__(self, mensagem: str, ordem_existente=None) -> None:
        super().__init__(mensagem)
        self.ordem_existente = ordem_existente


class OrdemServicoInativaError(OperacaoOrdemServicoError):
    pass


class RespostaJaRegistradaError(OperacaoOrdemServicoError):
    def __init__(self, mensagem: str, registro) -> None:
        super().__init__(mensagem)
        self.registro = registro


class OrdemServicoFacade:
    """Interface simplificada para abrir, mudar status, atribuir técnico e cancelar uma OS."""

    MENSAGEM_ALTERACAO_BLOQUEADA = "Esta ordem não pode mais ser alterada."
    MENSAGEM_CANCELAMENTO_BLOQUEADO = "Esta ordem já está encerrada ou cancelada."
    MENSAGEM_JA_AVALIADA = "Este atendimento já foi avaliado."
    MENSAGEM_CORRETIVA_DUPLICADA = (
        "Já existe uma ordem de serviço em andamento para este ativo. "
        "Em vez de abrir outra, você pode informar que também presenciou o problema."
    )
    MENSAGEM_OS_INATIVA = "Esta ordem não está mais em andamento (status atual: {status}); não é possível alterar participantes."

    def __init__(self, diretor=None, resolver_fabrica_processador=obter_fabrica_processador) -> None:
        self._diretor = diretor or OrdemServicoDiretor()
        self._resolver_fabrica_processador = resolver_fabrica_processador

    @staticmethod
    def esta_em_status_final(ordem_servico: OrdemServico) -> bool:
        return ordem_servico.status_ordem_servico in STATUS_FINAIS

    def garantir_alteracao_permitida(self, ordem_servico: OrdemServico) -> None:
        """Público para a view poder checar ANTES de validar o payload (mantém a precedência de erros da API)."""
        if self.esta_em_status_final(ordem_servico):
            raise OrdemServicoStatusFinalError(self.MENSAGEM_ALTERACAO_BLOQUEADA)

    @transaction.atomic
    def abrir(self, usuario, dados_validados: dict) -> OrdemServico:
        """Abre uma OS corretiva via Diretor/Builder e registra o histórico de abertura.

        `usuario` é None no fluxo anônimo do totem; nesse caso a OS fica sem
        solicitante e o histórico fica sem usuário.
        """
        dados = dict(dados_validados)

        dados.pop("status_ordem_servico", None)
        dados.pop("tipo_manutencao", None)

        localizacao = dados.pop("localizacao")
        descricao = dados.pop("descricao_servico")
        categoria_manutencao = dados.pop("categoria_manutencao", None)
        prioridade_urgencia = dados.pop("prioridade_urgencia", None)

        self._garantir_sem_corretiva_ativa(dados.get("ativo"), bloquear=True)

        solicitante = usuario if usuario is not None and usuario_tem_grupo(usuario, "SOLICITANTE") else None

        try:
            with transaction.atomic():
                ordem_servico = self._diretor.construir_corretiva_do_solicitante(
                    usuario=solicitante,
                    localizacao=localizacao,
                    descricao=descricao,
                    categoria_manutencao=categoria_manutencao,
                    prioridade_urgencia=prioridade_urgencia,
                    **dados,
                )
        except IntegrityError as erro:
            if "corretiva" in str(erro).lower():
                raise CorretivaDuplicadaError(
                    self.MENSAGEM_CORRETIVA_DUPLICADA, corretiva_ativa_do_ativo(dados.get("ativo"))
                ) from erro
            raise

        nome_solicitante = usuario.nome if usuario is not None else "Usuário Anônimo"

        registrar_historico(
            ordem_servico,
            usuario,
            f"Ordem de serviço aberta por {nome_solicitante}. Status inicial: {status_para_api(ordem_servico.status_ordem_servico)}.",
        )
        return ordem_servico

    @transaction.atomic
    def alterar_status(self, ordem_servico: OrdemServico, usuario, dados_validados: dict, motivo_tecnico: str = "") -> OrdemServico:
        """Aplica a edição validada e, se o status mudou, finaliza a OS pela pilha de decorators.

        O histórico da mudança de status é gravado pelo ComHistoricoDecorator,
        não aqui, para existir um único ponto que escreve esse registro.
        """
        self.garantir_alteracao_permitida(ordem_servico)

        status_anterior = ordem_servico.status_ordem_servico
        novo_status = dados_validados.get("status_ordem_servico")

        for campo, valor in dados_validados.items():
            setattr(ordem_servico, campo, valor)

        if novo_status and novo_status != status_anterior:
            definir_usuario_da_sessao(usuario)
            processador = self._montar_processador(ordem_servico, usuario, status_anterior)
            processador.finalizar(ordem_servico, motivo_tecnico)
        else:
            ordem_servico.save()

        return ordem_servico

    @transaction.atomic
    def atribuir_tecnico(self, ordem_servico: OrdemServico, tecnico, responsavel) -> OrdemServico:
        """Atribui o técnico; o responsável vira gestor da OS se ela ainda não tiver um, e ABERTA passa a APROVADA."""
        if not usuario_tem_grupo(tecnico, "TECNICO"):
            raise TecnicoInvalidoError("Usuário não é técnico.")

        gestor = ordem_servico.gestor or responsavel

        definir_usuario_da_sessao(responsavel)
        registrar_atribuicao(ordem_servico, gestor, tecnico)

        if ordem_servico.status_ordem_servico == ABERTA:
            status_anterior = ordem_servico.status_ordem_servico
            ordem_servico.status_ordem_servico = APROVADA
            ordem_servico.save(update_fields=["status_ordem_servico"])
            registrar_mudanca_status(ordem_servico, responsavel, status_anterior, APROVADA)

        ordem_servico.definir_responsaveis(tecnico, gestor)
        return ordem_servico

    @transaction.atomic
    def cancelar(self, ordem_servico: OrdemServico, usuario) -> OrdemServico:
        """Cancelamento lógico: a OS continua no banco com status CANCELADA."""
        if self.esta_em_status_final(ordem_servico):
            raise OrdemServicoStatusFinalError(self.MENSAGEM_CANCELAMENTO_BLOQUEADO)

        status_anterior = ordem_servico.status_ordem_servico
        definir_usuario_da_sessao(usuario)
        ordem_servico.status_ordem_servico = CANCELADA
        ordem_servico.dt_conclusao = timezone.now()
        ordem_servico.save()

        registrar_mudanca_status(ordem_servico, usuario, status_anterior, CANCELADA, f"OS cancelada por {usuario.nome}")
        return ordem_servico

    @transaction.atomic
    def validar(self, ordem_servico: OrdemServico, usuario, aprovada: bool, justificativa: str | None = None, evidencias=()) -> ValidacaoAtendimento:
        ordem_servico = self._bloquear(ordem_servico)

        resposta_existente = ValidacaoAtendimento.do_ciclo_atual(ordem_servico)
        if resposta_existente is not None:
            raise RespostaJaRegistradaError(
                f"Esta ordem já foi respondida por {resposta_existente.usuario.nome}. A decisão registrada não pode ser substituída.",
                resposta_existente,
            )

        if ordem_servico.status_ordem_servico != AGUARDANDO_VALIDACAO:
            raise OrdemServicoStatusInvalidoError(
                f"Esta ordem não está aguardando validação (status atual: {status_para_api(ordem_servico.status_ordem_servico)})."
            )

        agora = timezone.now()
        justificativa = (justificativa or "").strip() or None

        validacao, _ = ValidacaoAtendimento.objects.update_or_create(
            ordem_servico=ordem_servico,
            usuario=usuario,
            defaults={
                "resultado": RESULTADO_APROVADA if aprovada else RESULTADO_REPROVADA,
                "justificativa": justificativa,
                "nota": None,
                "comentario": None,
                "dt_validacao": agora,
            },
        )
        for arquivo in evidencias or ():
            EvidenciaValidacao.objects.create(validacao=validacao, arquivo=arquivo, nome_original=arquivo.name[:255], dt_upload=agora)

        status_anterior = ordem_servico.status_ordem_servico
        definir_usuario_da_sessao(usuario)

        if aprovada:
            ordem_servico.status_ordem_servico = CONCLUIDA
            ordem_servico.dt_conclusao = agora
            ordem_servico.save(update_fields=["status_ordem_servico", "dt_conclusao"])
            registrar_mudanca_status(ordem_servico, usuario, status_anterior, CONCLUIDA, f"Serviço aprovado por {usuario.nome}.")
            return validacao

        ordem_servico.status_ordem_servico = EM_EXECUCAO
        ordem_servico.dt_conclusao = None
        ordem_servico.save(update_fields=["status_ordem_servico", "dt_conclusao"])

        nome_tecnico = ordem_servico.tecnico_nome or "não definido"
        registrar_mudanca_status(
            ordem_servico, usuario, status_anterior, EM_EXECUCAO,
            f"Serviço reprovado por {usuario.nome}; retornou ao técnico {nome_tecnico}. Justificativa: {justificativa}",
        )
        self._alertar_gestor_reprovacao(ordem_servico, usuario, justificativa)
        return validacao

    @transaction.atomic
    def avaliar(self, ordem_servico: OrdemServico, usuario, nota: int, comentario: str | None = None) -> ValidacaoAtendimento:
        ordem_servico = self._bloquear(ordem_servico)

        avaliacao_existente = ValidacaoAtendimento.avaliacao_da_os(ordem_servico)
        if avaliacao_existente is not None:
            raise RespostaJaRegistradaError(self.MENSAGEM_JA_AVALIADA, avaliacao_existente)

        validacao = ValidacaoAtendimento.do_ciclo_atual(ordem_servico)
        if ordem_servico.status_ordem_servico != CONCLUIDA or validacao is None or not validacao.aprovada:
            raise OrdemServicoStatusInvalidoError(
                "A avaliação só é liberada após a validação aprovada do serviço "
                f"(status atual: {status_para_api(ordem_servico.status_ordem_servico)})."
            )

        comentario = (comentario or "").strip() or None

        if validacao.usuario_id == usuario.pk:
            avaliacao = validacao
            avaliacao.nota = nota
            avaliacao.comentario = comentario
            avaliacao.save(update_fields=["nota", "comentario"])
        else:
            avaliacao, _ = ValidacaoAtendimento.objects.update_or_create(
                ordem_servico=ordem_servico,
                usuario=usuario,
                defaults={
                    "resultado": None,
                    "justificativa": None,
                    "nota": nota,
                    "comentario": comentario,
                    "dt_validacao": timezone.now(),
                },
            )

        definir_usuario_da_sessao(usuario)
        ordem_servico.status_ordem_servico = ENCERRADA
        ordem_servico.save(update_fields=["status_ordem_servico"])
        registrar_mudanca_status(
            ordem_servico, usuario, CONCLUIDA, ENCERRADA,
            f"Atendimento avaliado por {usuario.nome} com nota {nota}/5.",
        )
        return avaliacao

    @transaction.atomic
    def presenciar(self, ordem_servico: OrdemServico, usuario) -> bool:
        ordem_servico = self._bloquear(ordem_servico)

        if usuario_ja_vinculado(ordem_servico, usuario):
            return False

        if not os_esta_ativa(ordem_servico):
            raise OrdemServicoInativaError(
                self.MENSAGEM_OS_INATIVA.format(status=status_para_api(ordem_servico.status_ordem_servico))
            )

        try:
            with transaction.atomic():
                OsParticipante.objects.create(ordem_servico=ordem_servico, usuario=usuario, dt_vinculo=timezone.now())
        except IntegrityError:
            return False

        registrar_historico(ordem_servico, usuario, f"{usuario.nome} informou que também presenciou o problema.")
        return True

    @transaction.atomic
    def deixar_de_presenciar(self, ordem_servico: OrdemServico, usuario) -> bool:
        ordem_servico = self._bloquear(ordem_servico)

        if not os_esta_ativa(ordem_servico):
            raise OrdemServicoInativaError(
                self.MENSAGEM_OS_INATIVA.format(status=status_para_api(ordem_servico.status_ordem_servico))
            )

        removidos, _ = OsParticipante.objects.filter(ordem_servico=ordem_servico, usuario=usuario).delete()
        if not removidos:
            return False

        registrar_historico(ordem_servico, usuario, f"{usuario.nome} removeu o vínculo de participante.")
        return True

    @staticmethod
    def _garantir_sem_corretiva_ativa(ativo, bloquear: bool = False) -> None:
        if ativo is None:
            return
        if bloquear:
            list(Ativo.objects.select_for_update().filter(pk=ativo.pk))
        existente = corretiva_ativa_do_ativo(ativo)
        if existente is not None:
            raise CorretivaDuplicadaError(OrdemServicoFacade.MENSAGEM_CORRETIVA_DUPLICADA, existente)

    @staticmethod
    def _bloquear(ordem_servico: OrdemServico) -> OrdemServico:
        return OrdemServico.objects.select_for_update().get(pk=ordem_servico.pk)

    @staticmethod
    def _alertar_gestor_reprovacao(ordem_servico: OrdemServico, usuario, justificativa: str | None) -> None:
        gestor = ordem_servico.gestor

        if gestor is None:
            registrar_historico(ordem_servico, usuario, "Alerta de reprovação: OS sem gestor definido; nenhum e-mail enviado.")
            return

        registrar_historico(ordem_servico, usuario, f"Alerta de reprovação enviado ao gestor {gestor.nome}.")

        assunto = f"OS #{ordem_servico.pk} reprovada pelo solicitante - TechOrder"
        mensagem = (
            f"Olá, {gestor.nome}.\n\n"
            f"A ordem de serviço #{ordem_servico.pk} foi reprovada por {usuario.nome} e voltou para execução.\n\n"
            f"Justificativa: {justificativa}\n\n"
            f"Acompanhe pelo sistema: {settings.FRONTEND_URL}"
        )
        email_gestor = gestor.email

        def _enviar():
            try:
                send_mail(assunto, mensagem, None, [email_gestor], fail_silently=True)
            except Exception:
                logger.exception("Falha ao enviar alerta de reprovação da OS #%s.", ordem_servico.pk)

        transaction.on_commit(_enviar)

    def _montar_processador(self, ordem_servico: OrdemServico, usuario, status_anterior: str) -> ProcessadorOrdemServico:
        """Factory Method escolhe o processador; a fachada o envolve em histórico e, por fora, em log."""
        processador = self._resolver_fabrica_processador(ordem_servico.tipo_manutencao).criar_processador()
        processador = ComHistoricoDecorator(processador, usuario=usuario, status_anterior=status_anterior)
        return ComLogDecorator(processador)
