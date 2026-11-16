import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass

from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction

from notificacao.models import Notificacao

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Mensagem:
    destinatario: object
    tipo: str
    titulo: str
    texto: str
    ordem_servico: object = None


class CanalNotificacao(ABC):
    @abstractmethod
    def enviar(self, mensagem: Mensagem):
        ...


class CanalSistema(CanalNotificacao):
    def enviar(self, mensagem: Mensagem):
        return Notificacao.objects.create(
            usuario=mensagem.destinatario,
            ordem_servico=mensagem.ordem_servico,
            tipo=mensagem.tipo,
            titulo=mensagem.titulo,
            mensagem=mensagem.texto,
        )


class CanalEmail(CanalNotificacao):
    def __init__(self, enviar_email=send_mail, agendar=transaction.on_commit):
        self._enviar_email = enviar_email
        self._agendar = agendar

    def enviar(self, mensagem: Mensagem):
        destinatario = getattr(mensagem.destinatario, 'email', None)
        if not destinatario:
            return None
        assunto = f"{mensagem.titulo} - TechOrder"
        corpo = f"{mensagem.texto}\n\nAcompanhe pelo sistema: {settings.FRONTEND_URL}"

        def _enviar():
            try:
                self._enviar_email(assunto, corpo, None, [destinatario], fail_silently=True)
            except Exception:
                logger.exception("Falha ao enviar e-mail de notificação para %s.", destinatario)

        self._agendar(_enviar)
        return None


class CanalComposto(CanalNotificacao):
    def __init__(self, canais=()):
        self._canais = list(canais)

    def adicionar(self, canal: CanalNotificacao) -> "CanalComposto":
        self._canais.append(canal)
        return self

    def enviar(self, mensagem: Mensagem):
        resultado = None
        for canal in self._canais:
            retorno = canal.enviar(mensagem)
            if resultado is None:
                resultado = retorno
        return resultado
