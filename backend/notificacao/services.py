import logging

from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction

from notificacao.models import Notificacao

logger = logging.getLogger(__name__)

TIPO_OS_ATRIBUIDA = 'OS_ATRIBUIDA'
TIPO_OS_REATRIBUIDA = 'OS_REATRIBUIDA'


def notificar(usuario, tipo, titulo, mensagem, ordem_servico=None, enviar_email=True):
    notificacao = Notificacao.objects.create(
        usuario=usuario, ordem_servico=ordem_servico, tipo=tipo, titulo=titulo, mensagem=mensagem,
    )

    if enviar_email and usuario.email:
        destinatario = usuario.email
        corpo = f"{mensagem}\n\nAcompanhe pelo sistema: {settings.FRONTEND_URL}"

        def _enviar():
            try:
                send_mail(f"{titulo} - TechOrder", corpo, None, [destinatario], fail_silently=True)
            except Exception:
                logger.exception("Falha ao enviar a notificação #%s por e-mail.", notificacao.pk)

        transaction.on_commit(_enviar)

    return notificacao
