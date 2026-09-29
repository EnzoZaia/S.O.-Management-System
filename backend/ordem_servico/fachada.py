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
from django.db import transaction
from django.utils import timezone

from ordem_servico.builders import OrdemServicoDiretor
from ordem_servico.models import OrdemServico
from ordem_servico.processadores import (
    ComHistoricoDecorator,
    ComLogDecorator,
    ProcessadorOrdemServico,
    obter_fabrica_processador,
)
from usuario.models import Usuario
from utils.historico import registrar_historico
from utils.permissions import usuario_tem_grupo

STATUS_FINAIS = ("ENCERRADA", "CANCELADA")


class OperacaoOrdemServicoError(Exception):
    """Regra de negócio violada numa operação da fachada; a mensagem vai direto para o cliente da API."""

    def __init__(self, mensagem: str) -> None:
        super().__init__(mensagem)
        self.mensagem = mensagem


class OrdemServicoStatusFinalError(OperacaoOrdemServicoError):
    """A OS já está ENCERRADA ou CANCELADA e não aceita mais a operação pedida."""


class TecnicoInvalidoError(OperacaoOrdemServicoError):
    """O usuário indicado para a atribuição não pertence ao grupo TECNICO."""


class OrdemServicoFacade:
    """Interface simplificada para abrir, mudar status, atribuir técnico e cancelar uma OS."""

    MENSAGEM_ALTERACAO_BLOQUEADA = "Esta ordem não pode mais ser alterada."
    MENSAGEM_CANCELAMENTO_BLOQUEADO = "Esta ordem já está encerrada ou cancelada."

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
        solicitante e o histórico é assinado pelo primeiro usuário do banco,
        já que a coluna id_usuario do histórico não aceita nulo.
        """
        dados = dict(dados_validados)

        dados.pop("status_ordem_servico", None)
        dados.pop("tipo_manutencao", None)

        localizacao = dados.pop("localizacao")
        descricao = dados.pop("descricao_servico")
        categoria_manutencao = dados.pop("categoria_manutencao", None)
        prioridade_urgencia = dados.pop("prioridade_urgencia", None)

        ordem_servico = self._diretor.construir_corretiva_do_solicitante(
            usuario=usuario,
            localizacao=localizacao,
            descricao=descricao,
            categoria_manutencao=categoria_manutencao,
            prioridade_urgencia=prioridade_urgencia,
            **dados,
        )

        if usuario is not None:
            usuario_historico = usuario
            nome_solicitante = usuario.nome
        else:
            usuario_historico = Usuario.objects.first()
            nome_solicitante = "Usuário Anônimo"

        registrar_historico(
            ordem_servico,
            usuario_historico,
            f"Ordem de serviço aberta por {nome_solicitante}. Status inicial: ABERTA.",
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
        ordem_servico.save()

        if novo_status and novo_status != status_anterior:
            processador = self._montar_processador(ordem_servico, usuario, status_anterior)
            processador.finalizar(ordem_servico, motivo_tecnico)

            if novo_status == "CONCLUIDA":
                ordem_servico.save()

        return ordem_servico

    @transaction.atomic
    def atribuir_tecnico(self, ordem_servico: OrdemServico, tecnico, responsavel) -> OrdemServico:
        """Atribui o técnico; o responsável vira gestor da OS se ela ainda não tiver um, e ABERTA passa a APROVADA."""
        if not usuario_tem_grupo(tecnico, "TECNICO"):
            raise TecnicoInvalidoError("Usuário não é técnico.")

        ordem_servico.tecnico = tecnico

        if ordem_servico.gestor is None:
            ordem_servico.gestor = responsavel

        if ordem_servico.status_ordem_servico == "ABERTA":
            ordem_servico.status_ordem_servico = "APROVADA"

        ordem_servico.save()

        registrar_historico(ordem_servico, responsavel, f"Técnico atribuído: {tecnico.nome}")
        return ordem_servico

    @transaction.atomic
    def cancelar(self, ordem_servico: OrdemServico, usuario) -> OrdemServico:
        """Cancelamento lógico: a OS continua no banco com status CANCELADA."""
        if self.esta_em_status_final(ordem_servico):
            raise OrdemServicoStatusFinalError(self.MENSAGEM_CANCELAMENTO_BLOQUEADO)

        ordem_servico.status_ordem_servico = "CANCELADA"
        ordem_servico.dt_conclusao = timezone.now()
        ordem_servico.save()

        registrar_historico(ordem_servico, usuario, f"OS cancelada por {usuario.nome}")
        return ordem_servico

    def _montar_processador(self, ordem_servico: OrdemServico, usuario, status_anterior: str) -> ProcessadorOrdemServico:
        """Factory Method escolhe o processador; a fachada o envolve em histórico e, por fora, em log."""
        processador = self._resolver_fabrica_processador(ordem_servico.tipo_manutencao).criar_processador()
        processador = ComHistoricoDecorator(processador, usuario=usuario, status_anterior=status_anterior)
        return ComLogDecorator(processador)
